const f=document.getElementById('f'),$=id=>document.getElementById(id),reg=f.dataset.mode==='register';
function toast(m,t){const d=document.createElement('div');d.className='toast '+(t||'');d.textContent=m;$('toasts').append(d);setTimeout(()=>d.remove(),4000)}
const q=new URLSearchParams(location.search).get('msg');
if(q==='expired')toast('Your session expired. Please log in again.','bad');if(q==='bye')toast('You have been logged out.');if(q==='registered')toast('Account created! Please log in.');
$('eye').onclick=()=>{const p=$('password');p.type=p.type==='password'?'text':'password'};
f.onsubmit=async e=>{e.preventDefault();const b={};['name','age','city','email','password','confirm'].forEach(k=>{if($(k))b[k]=$(k).value});
 const bad=Object.entries(b).find(([k,v])=>!String(v).trim());if(bad){$('err').textContent='Please fill in all fields.';return}
 if(reg&&b.password.length<8){$('err').textContent='Password must be at least 8 characters.';return}
 if(reg&&b.password!==b.confirm){$('err').textContent='Passwords do not match.';return}
 try{const r=await fetch(reg?'/api/register':'/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});const j=await r.json();
 if(!r.ok){$('err').textContent=j.error;toast(j.error,'bad');return}
 if(reg){toast('Account created! Redirecting to login…');setTimeout(()=>location.href='/login?msg=registered',900)}else location.href='/dashboard'}
 catch{toast('Could not reach the server.','bad')}};
