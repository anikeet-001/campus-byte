import React,{useEffect,useState} from 'react';
import {api,money} from './api';
const names={requested:'Awaiting kitchen',rejected:'Declined',waiting:'Waiting for a rider',assigned:'Rider assigned',picked_up:'On the way',delivered:'Delivered'};
export default function Orders({role}){
  const [orders,setOrders]=useState(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{
    let active=true,timer;
    async function poll(){try{const rows=await api('orders');if(active)setOrders(rows);}catch(e){if(active)setError(e.message);}
      finally{if(active)timer=setTimeout(poll,4000);}}
    poll();return()=>{active=false;clearTimeout(timer);};
  },[]);
  async function act(id,action){
    setBusy(true);setError('');try{await api('orders/'+id+'/'+action,'POST');setOrders(await api('orders'));}
    catch(e){setError(e.message);}finally{setBusy(false);}
  }
  return <><div className="eyebrow">{role.toUpperCase()} / LIVE ORDERS</div><h1>{role==='partner'?'Deliveries':'Orders'}<span>.</span></h1>
    {error&&<p role="alert">{error}</p>}{!orders?<p>Loading orders…</p>:!orders.length?<div className="panel"><h2>No orders yet</h2><p>{role==='partner'?'Accepted orders appear here when assigned to you.':role==='owner'?'Customer requests for your kitchen will appear here.':'Choose a kitchen and place your first order.'}</p></div>:orders.map(o=><article className="panel ticket" key={o.id}>
    <div className="split"><span className="eyebrow">TICKET #{o.id}</span><strong className="status">{names[o.status]}</strong></div><h2>{o.kitchen}</h2>
    {o.items.map(x=><p className="split" key={x.dish}><span>{x.quantity} × {x.name}</span>{money(x.quantity*x.paise)}</p>)}<div className="row"><span>Order total</span><strong>{money(o.total)}</strong></div>
    <small>Deliver to</small><strong>{o.address}</strong><div className="actions">{role==='owner'&&o.status==='requested'&&<><button disabled={busy} onClick={()=>act(o.id,'accept')}>Accept order</button><button disabled={busy} className="secondary" onClick={()=>act(o.id,'reject')}>Reject</button></>}
    {role==='partner'&&['assigned','picked_up'].includes(o.status)&&<button disabled={busy} onClick={()=>act(o.id,o.status==='assigned'?'pickup':'deliver')}>{o.status==='assigned'?'Confirm pickup':'Mark delivered'}</button>}</div></article>)}</>;
}
