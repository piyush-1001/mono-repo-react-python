import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useToastContext } from '@/context/ToastContext';
import { Button, ConfirmDialog, EmptyState, ErrorState, PageHeader, Pagination, Spinner } from '@/components/common';
import { Badge } from '@/components/common/Badge';
import { Modal } from '@/components/common/Modal';
import { Input } from '@/components/common/Input';
import { Select } from '@/components/common/Select';
import { encryptPayload, getPublicKey } from '@/lib/encryption';
import { createUser, listUsers, patchUserStatus } from '@/api/auth.api';
import { usePagination } from '@/hooks/usePagination';
import { useDisclosure } from '@/hooks/useDisclosure';
import { useDebounce } from '@/hooks/useDebounce';
import { formatDateTime, maskEmail } from '@/lib/format';
import { ROLE } from '@/lib/constants';
import { required, email, runValidators } from '@/lib/validators';

/**
 * Users management page — list, create (encrypted), activate/deactivate.
 * @returns {React.ReactElement}
 */
export function UsersPage() {
  const toast = useToastContext();
  const qc = useQueryClient();
  const { page, limit, setPage, setLimit, setTotal, total } = usePagination();
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 400);
  const [roleFilter, setRoleFilter] = useState('');
  const [toggleUser, setToggleUser] = useState(null);
  const createModal = useDisclosure();
  const toggleDialog = useDisclosure();

  // --- Create form state ---
  const [formValues, setFormValues] = useState({ firstName: '', lastName: '', email: '', phone: '', password: '', role: ROLE.STAFF });
  const [formErrors, setFormErrors] = useState({});

  const params = {
    search: debouncedSearch || undefined,
    page,
    limit,
    role: roleFilter || undefined,
  };

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['users', params],
    queryFn: () => listUsers(params),
    placeholderData: (prev) => prev,
  });

  const users = data?.items || [];
  const totalCount = data?.total || 0;

  const createMut = useMutation({
    mutationFn: async (values) => {
      const publicKey = getPublicKey();
      const encrypted = encryptPayload(values, publicKey);
      return createUser(encrypted);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      toast.addToast('User created successfully.', 'success');
      createModal.onClose();
      setFormValues({ firstName: '', lastName: '', email: '', phone: '', password: '', role: ROLE.STAFF });
      setFormErrors({});
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to create user.', 'error'),
  });

  const toggleMut = useMutation({
    mutationFn: ({ userId, isActive }) => patchUserStatus(userId, { isActive }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] });
      toast.addToast(`User ${toggleUser.isActive ? 'deactivated' : 'activated'}.`, 'success');
      toggleDialog.onClose();
      setToggleUser(null);
    },
    onError: (err) => toast.addToast(err?.message || 'Failed to update user.', 'error'),
  });

  function handleFormChange(e) {
    const { name, value } = e.target;
    setFormValues((prev) => ({ ...prev, [name]: value }));
    if (formErrors[name]) setFormErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleFormSubmit(e) {
    e.preventDefault();
    const { errors } = runValidators(
      {
        firstName: required,
        lastName: required,
        email: (v) => required(v, 'Email') || email(v),
        phone: required,
        password: required,
      },
      formValues,
    );
    if (Object.keys(errors).length) {
      setFormErrors(errors);
      return;
    }
    await createMut.mutateAsync(formValues);
  }

  return (
    <div className="page">
      <PageHeader
        title="Users"
        subtitle={`${totalCount} total users`}
        actions={<Button onClick={createModal.onOpen}>+ New User</Button>}
      />

      <div className="filters-bar">
        <input
          type="search"
          className="field__input"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search users"
        />
        <Select label="Role" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
          <option value="">All roles</option>
          <option value={ROLE.ADMIN}>Admin</option>
          <option value={ROLE.STAFF}>Staff</option>
          <option value={ROLE.USER}>User</option>
        </Select>
      </div>

      {isLoading ? (
        <div className="page-loader"><Spinner size="lg" /></div>
      ) : isError ? (
        <ErrorState onRetry={refetch} />
      ) : users.length === 0 ? (
        <EmptyState title="No users found" description="Try adjusting your filters." />
      ) : (
        <>
          <div className="table-wrap">
            <table className="table" aria-label="Users">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="table__row">
                    <td className="table__cell">{u.firstName} {u.lastName}</td>
                    <td className="table__cell table__cell--muted">{maskEmail(u.email)}</td>
                    <td className="table__cell">{u.phone}</td>
                    <td className="table__cell">
                      <Badge label={u.role} variant={u.role === 'ADMIN' ? 'info' : 'neutral'} />
                    </td>
                    <td className="table__cell">
                      <Badge label={u.isActive ? 'Active' : 'Inactive'} variant={u.isActive ? 'success' : 'danger'} />
                    </td>
                    <td className="table__cell table__cell--muted">{formatDateTime(u.createdAt)}</td>
                    <td className="table__cell table__cell--actions">
                      <Button
                        variant={u.isActive ? 'secondary' : 'ghost'}
                        size="sm"
                        onClick={() => { setToggleUser(u); toggleDialog.onOpen(); }}
                      >
                        {u.isActive ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            page={page}
            totalPages={Math.max(1, Math.ceil(totalCount / limit))}
            total={totalCount}
            limit={limit}
            onPageChange={setPage}
            onLimitChange={setLimit}
          />
        </>
      )}

      {/* Create User Modal */}
      <Modal isOpen={createModal.isOpen} onClose={createModal.onClose} title="New User" size="md">
        <form onSubmit={handleFormSubmit} noValidate>
          <div className="form-stack">
            <Input label="First Name" name="firstName" value={formValues.firstName} onChange={handleFormChange} error={formErrors?.firstName} required />
            <Input label="Last Name" name="lastName" value={formValues.lastName} onChange={handleFormChange} error={formErrors?.lastName} required />
            <Input label="Email" name="email" type="email" value={formValues.email} onChange={handleFormChange} error={formErrors?.email} required />
            <Input label="Phone" name="phone" value={formValues.phone} onChange={handleFormChange} error={formErrors?.phone} required />
            <Input label="Password" name="password" type="password" value={formValues.password} onChange={handleFormChange} error={formErrors?.password} required />
            <Select label="Role" name="role" value={formValues.role} onChange={handleFormChange}>
              <option value={ROLE.ADMIN}>Admin</option>
              <option value={ROLE.STAFF}>Staff</option>
              <option value={ROLE.USER}>User</option>
            </Select>
          </div>
          <div className="modal__footer">
            <Button type="button" variant="secondary" onClick={createModal.onClose} disabled={createMut.isPending}>Cancel</Button>
            <Button type="submit" loading={createMut.isPending}>Create User</Button>
          </div>
        </form>
      </Modal>

      {/* Activate / Deactivate Confirm */}
      <ConfirmDialog
        isOpen={toggleDialog.isOpen}
        onClose={toggleDialog.onClose}
        onConfirm={() => toggleUser && toggleMut.mutate({ userId: toggleUser.id, isActive: !toggleUser.isActive })}
        title={toggleUser?.isActive ? 'Deactivate User' : 'Activate User'}
        message={`${toggleUser?.isActive ? 'Deactivate' : 'Activate'} "${toggleUser?.firstName} ${toggleUser?.lastName}"?`}
        loading={toggleMut.isPending}
        variant="danger"
      />
    </div>
  );
}
