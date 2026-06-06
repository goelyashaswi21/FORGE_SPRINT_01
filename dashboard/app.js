/* app.js — SEO Command Center live cockpit */
const $ = (id) => document.getElementById(id);
let totals = { High: 0, Medium: 0, Low: 0, total: 0 };
let issueRows = [];
let sortCol = -1, sortAsc = true;
const sevOrder = { High: 0, Medium: 1, Low: 2 };

function log(msg) {
  const l = $("log"); if (l.querySelector(".empty")) l.innerHTML = "";
  const d = document.createElement("div"); d.textContent = "> " + msg; l.appendChild(d); l.scrollTop = l.scrollHeight;
}
function renderTable() {
  const tb = $("tbody");
  if (!issueRows.length) { tb.innerHTML = '<tr><td colspan="3" class="empty">Waiting…</td></tr>'; return; }
  let rows = [...issueRows];
  if (sortCol === 0) rows.sort((a,b) => (sevOrder[a.severity]||0)-(sevOrder[b.severity]||0));
  else if (sortCol === 1) rows.sort((a,b) => a.type.localeCompare(b.type));
  else if (sortCol === 2) rows.sort((a,b) => b.count-a.count);
  if (!sortAsc) rows.reverse();
  tb.innerHTML = rows.map(i => '<tr><td><span class="sev '+i.severity.toLowerCase()+'">'+i.severity+'</span></td><td>'+i.type+'</td><td>'+i.count+'</td></tr>').join("");
}
function sortTable(col) {
  if (sortCol===col) sortAsc=!sortAsc; else { sortCol=col; sortAsc=true; }
  renderTable();
}
function addIssue(i) {
  issueRows.push(i);
  totals[i.severity]=(totals[i.severity]||0)+1; totals.total++;
  $("c-total").textContent=totals.total; $("c-high").textContent=totals.High;
  $("c-med").textContent=totals.Medium; $("c-low").textContent=totals.Low;
  renderTable();
  const pct=Math.min(100,Math.round((issueRows.length/17)*100));
  $("progress-wrap").style.display="block"; $("progress-bar").style.width=pct+"%";
}
function handle({event,data}) {
  if (event==="snapshot") {
    if (data.site){$("meta").textContent="· "+data.site;$("urls").textContent=(data.urls||0)+" URLs";}
    (data.issues||[]).forEach(addIssue);
  } else if (event==="loaded") {
    $("meta").textContent="· "+data.site; $("urls").textContent=data.urls+" URLs";
    log("Loaded "+data.urls+" URLs from "+data.site);
    issueRows=[]; totals={High:0,Medium:0,Low:0,total:0}; renderTable();
  } else if (event==="issue") {
    addIssue(data); log("Found "+data.count+" x "+data.type);
  } else if (event==="summary") {
    log("Audit complete: "+data.total_issues+" issue types");
  } else if (event==="recommendations") {
    const recs=data.recommendations||[];
    if (recs.length){$("recs-card").style.display="block";$("recs-list").innerHTML=recs.map(r=>"<li>"+r+"</li>").join("");}
  } else if (event==="fixes") {
    const t=(data.titles||[]).length,r=(data.redirect_map||[]).length;
    $("fixes-body").innerHTML='<div class="fixes-counts"><span><b>'+t+'</b> title rewrites</span><span><b>'+r+'</b> redirect mappings</span></div>';
    log("Fixes ready: "+t+" titles, "+r+" redirects");
  } else if (event==="exported") {
    $("export").innerHTML="<b>report.html written</b><br><span style='color:#c8c5be;font-size:12px'>Email outputs/report.html to the client.</span>";
    $("done-banner").style.display="block"; $("progress-bar").style.width="100%";
    setTimeout(()=>{$("progress-wrap").style.display="none";},1000);
  } else if (event==="saved") { log("report.json saved"); }
}
const es=new EventSource("/events");
es.onmessage=(m)=>{try{handle(JSON.parse(m.data));}catch(e){}};
