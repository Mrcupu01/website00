const form = document.getElementById('certForm');
const keys = ['member_name','title','intro','description','period','issued_date','community','signer','role','certificate_id'];
function updatePreview(){
  keys.forEach(key=>{
    const input=form.elements[key];
    const target=document.querySelectorAll(`[data-key="${key}"]`);
    if(input) target.forEach(el=>el.textContent=input.value || '');
  });
  const name=document.querySelector('[data-key="member_name"]');
  if(name){let size=49;name.style.fontSize='';while(name.scrollWidth>name.parentElement.clientWidth*.95 && size>18){size-=2;name.style.fontSize=size+'px';}}
}
form.addEventListener('input',updatePreview);
document.getElementById('reset').addEventListener('click',()=>{
  const defaults={member_name:'Nama Member',title:'CERTIFICATE OF MEMBERSHIP',intro:'This certificate is proudly presented to',description:'In recognition of being part of the Mineblox Community.',period:'2025 – 2027',issued_date:new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'long',year:'numeric'}),community:'MINEBLOX COMMUNITY',signer:'Mineblox Team',role:'Community Representative'};
  Object.entries(defaults).forEach(([k,v])=>form.elements[k].value=v);
  updatePreview();
});
updatePreview();
