import React, { useEffect, useState } from "react";
import { API_BASE } from "../config";
import { useAuth } from "../AuthContext";

function AdminPage() {
  const { auth, authHeader } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [roomForm, setRoomForm] = useState({ room_name: "", capacity: 10 });
  const [trainers, setTrainers] = useState([]);
  const [classes, setClasses] = useState([]);
  const [classForm, setClassForm] = useState({ class_name: "", trainer_id: "", room_id: "", class_time: "", capacity: 10 });
  const [equipment, setEquipment] = useState([]);
  const [equipForm, setEquipForm] = useState({ equipment_name: "", room_id: "", status: "OPERATIONAL" });
  const [maintenance, setMaintenance] = useState([]);
  const [maintenanceDraft, setMaintenanceDraft] = useState({});
  const [invoices, setInvoices] = useState([]);
  const [invoiceForm, setInvoiceForm] = useState({ member_id: "", due_date: "", description: "", quantity: 1, unit_price: 0 });
  const [paymentDrafts, setPaymentDrafts] = useState({});

  const apiFetch = (path, options = {}) =>
    fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { ...(options.headers || {}), ...authHeader },
    });

  useEffect(() => {
    if (!auth || auth.role !== "admin") return;
    fetchRooms();
    fetchTrainers();
    fetchClasses();
    fetchEquipment();
    fetchMaintenance();
    fetchInvoices();
  }, [auth]);

  const fetchRooms = async () => {
    const res = await apiFetch(`/rooms`);
    setRooms(await res.json());
  };

  const fetchTrainers = async () => {
    const res = await apiFetch(`/trainers`);
    setTrainers(await res.json());
  };

  const fetchClasses = async () => {
    const res = await apiFetch(`/admin/classes`);
    setClasses(await res.json());
  };

  const fetchEquipment = async () => {
    const res = await apiFetch(`/admin/equipment`);
    setEquipment(await res.json());
  };

  const fetchMaintenance = async () => {
    const res = await apiFetch(`/admin/maintenance`);
    setMaintenance(await res.json());
  };

  const fetchInvoices = async () => {
    const res = await apiFetch(`/admin/invoices`);
    setInvoices(await res.json());
  };

  const addRoom = async () => {
    await apiFetch(`/admin/rooms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(roomForm)
    });
    setRoomForm({ room_name: "", capacity: 10 });
    fetchRooms();
  };

  const addClass = async () => {
    await apiFetch(`/admin/classes`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...classForm,
        trainer_id: classForm.trainer_id ? Number(classForm.trainer_id) : null,
        room_id: classForm.room_id ? Number(classForm.room_id) : null,
        capacity: Number(classForm.capacity)
      })
    });
    setClassForm({ class_name: "", trainer_id: "", room_id: "", class_time: "", capacity: 10 });
    fetchClasses();
  };

  const addEquipment = async () => {
    await apiFetch(`/admin/equipment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...equipForm,
        room_id: equipForm.room_id ? Number(equipForm.room_id) : null
      })
    });
    setEquipForm({ equipment_name: "", room_id: "", status: "OPERATIONAL" });
    fetchEquipment();
  };

  const logMaintenance = async (equipment_id) => {
    const note = maintenanceDraft[equipment_id];
    if (!note) return;
    await apiFetch(`/admin/equipment/${equipment_id}/maintenance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue_description: note })
    });
    setMaintenanceDraft({ ...maintenanceDraft, [equipment_id]: "" });
    fetchMaintenance();
  };

  const createInvoice = async () => {
    await apiFetch(`/admin/invoices`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        member_id: Number(invoiceForm.member_id),
        due_date: invoiceForm.due_date || null,
        items: [
          {
            description: invoiceForm.description,
            quantity: Number(invoiceForm.quantity),
            unit_price: Number(invoiceForm.unit_price)
          }
        ]
      })
    });
    setInvoiceForm({ member_id: "", due_date: "", description: "", quantity: 1, unit_price: 0 });
    fetchInvoices();
  };

  const payInvoice = async (invoice_id, remaining) => {
    const amount = paymentDrafts[invoice_id] ?? remaining;
    await apiFetch(`/admin/invoices/${invoice_id}/payments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount: Number(amount) })
    });
    fetchInvoices();
  };

  if (!auth || auth.role !== "admin") {
    return <p className="muted">Admins only. Please log in with an admin account.</p>;
  }

  return (
    <section className="section stack">
      <header className="card stack">
        <h1 style={{ color: "#0b1224" }}>Admin Dashboard</h1>
        <p className="muted" style={{ color: "#1f2937" }}>Manage rooms, classes, equipment, maintenance, and billing.</p>
      </header>

      <div className="grid-2">
        <article className="card stack">
          <h2>Rooms</h2>
          <div className="row">
            <input placeholder="Room name" value={roomForm.room_name} onChange={e => setRoomForm({...roomForm, room_name: e.target.value})}/>
            <input type="number" placeholder="Capacity" value={roomForm.capacity} onChange={e => setRoomForm({...roomForm, capacity: e.target.value})}/>
            <button onClick={addRoom}>Add Room</button>
          </div>
          <div className="stack">
            {rooms.map(r => (
              <div key={r.room_id} className="row" style={{ justifyContent: "space-between" }}>
                <span>{r.room_name}</span>
                <span className="pill">Cap {r.capacity}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="card stack">
          <h2>Classes</h2>
          <div className="row">
            <input placeholder="Class name" value={classForm.class_name} onChange={e => setClassForm({...classForm, class_name: e.target.value})}/>
            <select value={classForm.trainer_id} onChange={e => setClassForm({...classForm, trainer_id: e.target.value})}>
              <option value="">Trainer</option>
              {trainers.map(t => <option key={t.trainer_id} value={t.trainer_id}>{t.full_name}</option>)}
            </select>
            <select value={classForm.room_id} onChange={e => setClassForm({...classForm, room_id: e.target.value})}>
              <option value="">Room</option>
              {rooms.map(r => <option key={r.room_id} value={r.room_id}>{r.room_name}</option>)}
            </select>
            <input type="datetime-local" value={classForm.class_time} onChange={e => setClassForm({...classForm, class_time: e.target.value})}/>
            <input type="number" value={classForm.capacity} onChange={e => setClassForm({...classForm, capacity: e.target.value})}/>
            <button onClick={addClass}>Create</button>
          </div>
          <div className="stack">
            {classes.map(c => (
              <div key={c.class_id} className="row" style={{ justifyContent: "space-between" }}>
                <div>
                  <strong>{c.class_name}</strong>
                  <div className="muted">{new Date(c.class_time).toLocaleString()}</div>
                </div>
                <span className="pill">{c.status}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      <article className="card stack">
        <h2>Equipment & Maintenance</h2>
        <div className="row">
          <input placeholder="Equipment name" value={equipForm.equipment_name} onChange={e => setEquipForm({...equipForm, equipment_name: e.target.value})}/>
          <select value={equipForm.room_id} onChange={e => setEquipForm({...equipForm, room_id: e.target.value})}>
            <option value="">Room</option>
            {rooms.map(r => <option key={r.room_id} value={r.room_id}>{r.room_name}</option>)}
          </select>
          <button onClick={addEquipment}>Add Equipment</button>
        </div>
        <div className="stack">
          {equipment.map(eq => (
            <div key={eq.equipment_id} className="row" style={{ alignItems: "center", gap: "0.5rem" }}>
              <span>{eq.equipment_name}</span>
              <span className="pill">{eq.status}</span>
              <input
                placeholder="Log issue"
                value={maintenanceDraft[eq.equipment_id] || ""}
                onChange={e => setMaintenanceDraft({...maintenanceDraft, [eq.equipment_id]: e.target.value})}
              />
              <button className="secondary" onClick={() => logMaintenance(eq.equipment_id)}>Log</button>
            </div>
          ))}
        </div>
        <h4>Recent Maintenance</h4>
        <div className="stack">
          {maintenance.map(m => (
            <div key={m.log_id} className="row" style={{ justifyContent: "space-between" }}>
              <span>Eq #{m.equipment_id}: {m.issue_description}</span>
              <span className="pill">{m.status}</span>
            </div>
          ))}
        </div>
      </article>

      <article className="card stack">
        <h2>Billing</h2>
        <div className="row">
          <input placeholder="Member ID" value={invoiceForm.member_id} onChange={e => setInvoiceForm({...invoiceForm, member_id: e.target.value})}/>
          <input type="date" value={invoiceForm.due_date} onChange={e => setInvoiceForm({...invoiceForm, due_date: e.target.value})}/>
          <input placeholder="Description" value={invoiceForm.description} onChange={e => setInvoiceForm({...invoiceForm, description: e.target.value})}/>
          <input type="number" placeholder="Qty" value={invoiceForm.quantity} onChange={e => setInvoiceForm({...invoiceForm, quantity: e.target.value})}/>
          <input type="number" placeholder="Unit price" value={invoiceForm.unit_price} onChange={e => setInvoiceForm({...invoiceForm, unit_price: e.target.value})}/>
          <button onClick={createInvoice}>Create Invoice</button>
        </div>
        <div className="grid-2">
          {invoices.map(inv => {
            const paid = inv.payments?.reduce((sum, p) => sum + (p.amount || 0), 0) || 0;
            const remaining = (inv.total_amount || 0) - paid;
            return (
              <div key={inv.invoice_id} className="card stack" style={{ borderColor: "var(--muted-border-color)" }}>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <strong>Invoice #{inv.invoice_id}</strong>
                  <span className="pill">{inv.status}</span>
                </div>
                <div className="muted">Member {inv.member_id}</div>
                <div>Items: {inv.items?.map(it => `${it.description} (${it.quantity} x ${it.unit_price})`).join(", ")}</div>
                <div>Paid ${paid} | Remaining ${remaining}</div>
                {remaining > 0 && (
                  <div className="row">
                    <input
                      type="number"
                      value={paymentDrafts[inv.invoice_id] ?? remaining}
                      onChange={e => setPaymentDrafts({...paymentDrafts, [inv.invoice_id]: e.target.value})}
                    />
                    <button onClick={() => payInvoice(inv.invoice_id, remaining)}>Record Payment</button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </article>
    </section>
  );
}

export default AdminPage;
