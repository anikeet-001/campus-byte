import React, { useEffect, useState } from "react";
import { api, money } from "./api";
export default function Menu() {
  const [data, setData] = useState(null),
    [edit, setEdit] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const refresh = () => api("menu").then(setData);
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, []);
  async function mutate(work) {
    setBusy(true);
    setError("");
    try {
      await work();
      await refresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function submit(e) {
    e.preventDefault();
    const form = e.currentTarget;
    const body = {
      name: form.elements.name.value,
      paise: Math.round(Number(form.elements.price.value) * 100),
    };
    mutate(async () => {
      await api(edit ? "menu/" + edit.id : "menu", edit ? "PUT" : "POST", body);
      form.reset();
      setEdit(null);
    });
  }
  return (
    <>
      <div className="eyebrow">OWNER / {data?.name}</div>
      <h1>
        Kitchen menu<span>.</span>
      </h1>
      {error && <p role="alert">{error}</p>}
      <div className="columns">
        <section className="panel">
          <h2>Available dishes</h2>
          {data && !data.menu.length && (
            <p>Add your first dish to open for orders.</p>
          )}
          {data?.menu.map((d) => (
            <div className="row" key={d.id}>
              <div>
                <strong>{d.name}</strong>
                <small>{money(d.paise)}</small>
              </div>
              <div className="actions">
                <button
                  className="secondary"
                  disabled={busy}
                  onClick={() => setEdit(d)}
                >
                  Edit
                </button>
                <button
                  className="link"
                  disabled={busy}
                  onClick={() => {
                    if (window.confirm("Remove " + d.name + " from your menu?"))
                      mutate(async () => {
                        await api("menu/" + d.id, "DELETE");
                        if (edit?.id === d.id) setEdit(null);
                      });
                  }}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </section>
        <form key={edit?.id || "new"} className="panel" onSubmit={submit}>
          <h2>{edit ? "Edit dish" : "Add a dish"}</h2>
          <label>
            Dish name
            <input
              name="name"
              defaultValue={edit?.name}
              maxLength="120"
              required
            />
          </label>
          <label>
            Price in rupees
            <input
              type="number"
              name="price"
              min=".01"
              max="100000"
              step=".01"
              defaultValue={edit ? edit.paise / 100 : ""}
              required
            />
          </label>
          <button disabled={busy}>Save dish</button>
          {edit && (
            <button
              className="link"
              type="button"
              onClick={() => setEdit(null)}
            >
              Cancel
            </button>
          )}
        </form>
      </div>
    </>
  );
}
