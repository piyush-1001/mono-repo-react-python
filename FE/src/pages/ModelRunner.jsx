import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { listModels, runModel } from '../api/client';

// A page that runs whatever model is picked, using the input schema the
// catalogue publishes.
//
// The form is generated rather than hand-written: every entry in /api/models
// carries the fields of its request model, so a model added on the Python side
// turns up here as a working form without a change to this file. What a
// generated form cannot know is what the input is supposed to look like, so
// the model's own description is shown above the fields.

const initialValues = (parameters) =>
  Object.fromEntries(
    parameters.map((parameter) => [
      parameter.name,
      parameter.type === 'boolean' ? Boolean(parameter.default) : parameter.default ?? '',
    ]),
  );

// Turn the form state into a request body. The types come from the schema, so
// the page does not have to know what any particular model expects.
const buildBody = (parameters, values) => {
  const body = {};

  for (const parameter of parameters) {
    const raw = values[parameter.name];

    if (parameter.type === 'boolean') {
      body[parameter.name] = Boolean(raw);
    } else if (parameter.type === 'integer' || parameter.type === 'number') {
      // An empty number field is not a number. Sending null lets the API say
      // which field was wrong, instead of sending NaN, which JSON turns into
      // null anyway and the validator describes as a missing value.
      body[parameter.name] = raw === '' ? null : Number(raw);
    } else if (parameter.type === 'text-list') {
      body[parameter.name] = String(raw)
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean);
    } else if (parameter.type === 'json') {
      // The one model with a JSON parameter takes a list of tasks. An empty
      // field becomes an empty list, which the API rejects with a message
      // about the list being empty - the field was never going to be valid.
      body[parameter.name] = raw === '' ? [] : JSON.parse(raw);
    } else {
      body[parameter.name] = raw;
    }
  }

  return body;
};

function ModelRunner() {
  const [models, setModels] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await listModels();
      const list = data.models || [];
      setModels(list);
      if (list.length > 0) {
        setSelectedId(list[0].id);
        setValues(initialValues(list[0].parameters || []));
      }
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const selected = models.find((model) => model.id === selectedId) || null;
  const parameters = selected?.parameters || [];

  const choose = (id) => {
    const model = models.find((entry) => entry.id === id);
    setSelectedId(id);
    setValues(initialValues(model?.parameters || []));
    setResult(null);
    setError('');
  };

  const update = (name, value) => {
    setValues((previous) => ({ ...previous, [name]: value }));
  };

  const run = async () => {
    if (!selected) return;
    setLoading(true);
    setError('');
    try {
      // JSON.parse throws on a malformed field, and the message it throws is
      // about the browser's parser rather than about the field, so the parse
      // error is caught separately from the API error below.
      let body;
      try {
        body = buildBody(parameters, values);
      } catch (err) {
        setError(`One of the fields is not valid JSON: ${err.message}`);
        return;
      }
      setResult(await runModel(selected, body));
    } catch (err) {
      setError(err.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page">
      <section className="card">
        <p className="eyebrow">Catalogue · Any model</p>
        <h1>Model Runner</h1>
        <p className="subtitle">
          Every model the API exposes, with an input form built from its own
          schema. Pick one, fill it in, and run it.
        </p>

        <div className="form">
          <label htmlFor="model">Model</label>
          <select
            id="model"
            value={selectedId}
            onChange={(e) => choose(e.target.value)}
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>

        {selected && (
          <p className="muted">
            <code>
              {selected.method} {selected.endpoint}
            </code>{' '}
            &mdash; {selected.description}
          </p>
        )}

        <div className="form">
          {parameters.map((parameter) => (
            <div key={parameter.name}>
              <label htmlFor={`param-${parameter.name}`}>
                {parameter.name}
                {parameter.required ? '' : ' (optional)'}
              </label>

              {parameter.type === 'boolean' ? (
                <input
                  id={`param-${parameter.name}`}
                  type="checkbox"
                  checked={Boolean(values[parameter.name])}
                  onChange={(e) => update(parameter.name, e.target.checked)}
                />
              ) : parameter.type === 'text-list' || parameter.type === 'json' ? (
                <textarea
                  id={`param-${parameter.name}`}
                  rows={parameter.type === 'json' ? 5 : 3}
                  value={values[parameter.name] ?? ''}
                  onChange={(e) => update(parameter.name, e.target.value)}
                  placeholder={
                    parameter.type === 'json' ? '[{"id": 1, "title": "..."}]' : 'one per line'
                  }
                />
              ) : (
                <input
                  id={`param-${parameter.name}`}
                  type={parameter.type === 'integer' || parameter.type === 'number' ? 'number' : 'text'}
                  value={values[parameter.name] ?? ''}
                  onChange={(e) => update(parameter.name, e.target.value)}
                />
              )}
            </div>
          ))}
        </div>

        <button onClick={run} disabled={loading || !selected}>
          {loading ? 'Running...' : 'Run model'}
        </button>

        {error && <p className="error-msg">{error}</p>}

        {result && (
          <div className="response-box">
            <h2>Result</h2>
            <pre className="export-preview">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}

        <Link to="/models" className="nav-link">
          ← Models
        </Link>
      </section>
    </main>
  );
}

export default ModelRunner;
