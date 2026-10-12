import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useToastContext } from '@/context/ToastContext';
import { Button, Input } from '@/components/common';
import { email, required, runValidators } from '@/lib/validators';
import { passwordStrength } from '@/lib/validators';

/**
 * Login page with encrypted credential submission.
 * @returns {React.ReactElement}
 */
export function LoginPage() {
  const { signIn, isSubmitting, error } = useAuth();
  const { addToast } = useToastContext();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  const [values, setValues] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});

  function handleChange(e) {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const { errors: errs } = runValidators(
      { email, password: required },
      { ...values, password: values.password },
    );
    if (errs.email) errs.email = 'Invalid email address';
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }

    try {
      await signIn(values.email, values.password);
      addToast('Welcome back!', 'success');
      navigate(from, { replace: true });
    } catch {
      addToast('Invalid credentials. Please try again.', 'error');
    }
  }

  const strength = passwordStrength(values.password);

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__header">
          <h1 className="login-card__title">Inventory Dashboard</h1>
          <p className="login-card__subtitle">Sign in to your account</p>
        </div>

        {error && (
          <div className="alert alert--error" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="login-form">
          <Input
            label="Email address"
            id="email"
            name="email"
            type="email"
            value={values.email}
            onChange={handleChange}
            error={errors?.email}
            required
            autoComplete="email"
            placeholder="you@example.com"
          />
          <div>
            <Input
              label="Password"
              id="password"
              name="password"
              type="password"
              value={values.password}
              onChange={handleChange}
              error={errors?.password}
              required
              autoComplete="current-password"
            />
            {values.password && (
              <div className="strength-meter" aria-live="polite">
                <div className="strength-meter__bar">
                  {[1, 2, 3, 4].map((n) => (
                    <span
                      key={n}
                      className={`strength-meter__segment ${
                        n <= strength.score ? 'strength-meter__segment--filled' : ''
                      }`}
                      style={{ backgroundColor: n <= strength.score ? strength.color : undefined }}
                    />
                  ))}
                </div>
                <span className="strength-meter__label" style={{ color: strength.color }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          <Button type="submit" loading={isSubmitting} className="login-form__submit">
            Sign in
          </Button>
        </form>
      </div>
    </div>
  );
}
