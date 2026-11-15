import React, {useEffect,useState} from 'react';
import {api,money} from './api';
import {useNavigate} from 'react-router-dom';

export default function Kitchens() {
  const [places,setPlaces]=useState(null), [choice,setChoice]=useState(0), [cart,setCart]=useState({});
  const [error,setError]=useState(''), [busy,setBusy]=useState(false);
  const navigate=useNavigate();
  useEffect(()=>{api('restaurants').then(setPlaces).catch(e=>setError(e.message));},[]);
  const place=places?.find(x=>x.id===choice)||places?.[0];
  const lines=(place?.menu||[]).filter(x=>cart[x.id]>0);
  const total=lines.reduce((sum,x)=>sum+x.paise*cart[x.id],0);
  function change(id,delta){setCart(old=>({...old,[id]:Math.max(0,Math.min(30,(old[id]||0)+delta))}));}
  async function order(event){
    event.preventDefault();setBusy(true);setError('');
    try {await api('orders','POST',{restaurant:place.id,address:event.target.address.value,items:lines.map(x=>({dish:x.id,quantity:cart[x.id]}))});navigate('/orders');}
    catch(e){setError(e.message);}finally{setBusy(false);}
  }
  return <><div className="eyebrow">CUSTOMER / ORDER FOOD</div><h1>Campus kitchens<span>.</span></h1>
    {error&&<p role="alert">{error}</p>}{!places?'Loading kitchens…':!place?<p>No kitchens yet. A restaurant owner can register and add a menu.</p>:<>
    <label className="picker">Kitchen<select value={place.id} onChange={e=>{setChoice(Number(e.target.value));setCart({});}}>{places.map(x=><option key={x.id} value={x.id}>{x.name}</option>)}</select></label>
    <div className="columns"><section className="panel"><div className="eyebrow">TODAY’S MENU</div><h2>{place.name}</h2>{!place.menu.length&&<p>This kitchen hasn’t listed any dishes yet.</p>}
    {place.menu.map(d=><div className="row" key={d.id}><div><strong>{d.name}</strong><small>{money(d.paise)}</small></div><div className="step">
    <button aria-label={'Remove one '+d.name} disabled={!cart[d.id]} onClick={()=>change(d.id,-1)}>−</button><b>{cart[d.id]||0}</b><button aria-label={'Add one '+d.name} disabled={cart[d.id]===30} onClick={()=>change(d.id,1)}>+</button></div></div>)}</section>
    <form className="panel receipt" onSubmit={order}><div className="eyebrow">ORDER TICKET</div><h2>Your order</h2>{lines.length?lines.map(x=><p className="split" key={x.id}><span>{cart[x.id]} × {x.name}</span>{money(cart[x.id]*x.paise)}</p>):<p>Choose a dish to start your order.</p>}<div className="row"><b>Total</b><b>{money(total)}</b></div><label>Delivery location<input name="address" placeholder="Hostel, block and room" required maxLength="120"/></label><button disabled={!lines.length||busy}>Place order →</button></form></div></>}</>;
}
