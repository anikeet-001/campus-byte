import React,{useState} from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Routes,Route,NavLink,Navigate} from 'react-router-dom';
import {readSession} from './api';
import Auth from './Auth';
import Kitchens from './Kitchens';
import Orders from './Orders';
import Menu from './Menu';
import './style.css';
function App(){
  const [session,setSession]=useState(readSession);
  const role=session?.user.role;
  const home=role==='customer'?'/kitchens':role==='owner'?'/menu':'/orders';
  function finish(value){sessionStorage.setItem('campus.session',JSON.stringify(value));setSession(value);}
  return <><header><div className="brand"><b>CB</b>Campus Byte</div>{session&&<nav>{role!=='partner'&&<NavLink to={home}>{role==='owner'?'Kitchen menu':'Kitchens'}</NavLink>}<NavLink to="/orders">{role==='partner'?'Deliveries':'Orders'}</NavLink><button className="link" onClick={()=>{sessionStorage.removeItem('campus.session');setSession(null);}}>Sign out</button></nav>}</header>
  <main><Routes>{session?<><Route path="/orders" element={<Orders role={role}/>}/>{role==='customer'&&<Route path="/kitchens" element={<Kitchens/>}/>}
  {role==='owner'&&<Route path="/menu" element={<Menu/>}/>}<Route path="*" element={<Navigate replace to={home}/>}/></>:<><Route path="/signin" element={<Auth finish={finish}/>}/><Route path="*" element={<Navigate replace to="/signin"/>}/></>}</Routes></main></>;
}
createRoot(document.getElementById('root')).render(<BrowserRouter><App/></BrowserRouter>);
