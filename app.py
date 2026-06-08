"""
app.py — Unified launcher: Flask (port 5000) + Gradio (port 7860) run together
Run:  python app.py
  → Dashboard:  http://localhost:5000
  → AI Chat:    http://localhost:7860
"""
import os, sys, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from flask import Flask, request, jsonify, send_from_directory
import gradio as gr
from query import ask

# ═══════════════════════════════════════════════════════════════════
# FLASK — serves the interactive HTML dashboard + /ask API endpoint
# ═══════════════════════════════════════════════════════════════════
flask_app = Flask(__name__, static_folder="static", static_url_path="")

@flask_app.route("/")
def index():
    return send_from_directory("static", "index.html")

@flask_app.route("/ask", methods=["POST"])
def handle_ask():
    data = request.get_json()
    question  = (data or {}).get("question", "").strip()
    professor = (data or {}).get("professor", None)   # optional metadata filter
    if not question:
        return jsonify({"error": "No question provided."}), 400
    result = ask(question, professor=professor)
    return jsonify({
        "answer":  result["answer"],
        "sources": result["sources"],
        "chunks": [
            {
                "source":   c["source"],
                "text":     c["text"][:300],
                "distance": round(c["distance"], 4),
            }
            for c in result["chunks"]
        ],
        "filtered_by": professor,   # echo back so the UI can show it
    })

def run_flask():
    print("  Dashboard  → http://localhost:5000")
    flask_app.run(port=5000, debug=False, use_reloader=False)

# ═══════════════════════════════════════════════════════════════════
# GRADIO — AI chat tab, same editorial style
# ═══════════════════════════════════════════════════════════════════
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Outfit:wght@300;400;500;600&display=swap');
:root{--ink:#0f0e17;--paper:#faf9f6;--warm:#f5f0e8;--gold:#c9a84c;--sage:#4a7c59;--border:#e2ddd5;--muted:#9a9080;--slate:#5a6a7a;}
*{box-sizing:border-box;}
body,.gradio-container{background:var(--paper)!important;font-family:'Outfit',sans-serif!important;color:var(--ink)!important;}
.gr-panel,[data-testid="block"],.block,.form,.gr-group{background:transparent!important;border:none!important;border-radius:0!important;box-shadow:none!important;}
label span{color:var(--muted)!important;font-size:10px!important;font-weight:600!important;letter-spacing:.18em!important;text-transform:uppercase!important;}
textarea,input[type="text"]{background:#fff!important;border:1px solid var(--border)!important;border-radius:3px!important;color:var(--ink)!important;font-family:'Outfit',sans-serif!important;font-size:.95rem!important;font-weight:300!important;caret-color:var(--gold)!important;transition:border-color .2s,box-shadow .2s!important;}
textarea:focus,input[type="text"]:focus{border-color:var(--gold)!important;box-shadow:0 0 0 3px #c9a84c14!important;outline:none!important;}
textarea::placeholder{color:#c0bab2!important;font-style:italic!important;}
#ask-btn{background:var(--ink)!important;border:2px solid var(--ink)!important;border-radius:3px!important;color:#fff!important;font-family:'Outfit',sans-serif!important;font-size:.8rem!important;font-weight:600!important;letter-spacing:.14em!important;text-transform:uppercase!important;transition:background .2s,color .2s,transform .15s!important;}
#ask-btn:hover{background:var(--gold)!important;border-color:var(--gold)!important;color:var(--ink)!important;transform:translateY(-1px)!important;}
.gr-samples-table td,.samples-table td{background:var(--warm)!important;border:1px solid var(--border)!important;border-radius:2px!important;color:var(--slate)!important;font-size:.78rem!important;font-family:'Outfit',sans-serif!important;padding:6px 14px!important;cursor:pointer!important;transition:background .18s,border-color .18s!important;}
.gr-samples-table td:hover,.samples-table td:hover{background:var(--gold)!important;border-color:var(--gold)!important;color:var(--ink)!important;}
#answer-box textarea{background:#fff!important;border:1px solid var(--border)!important;border-left:3px solid var(--gold)!important;border-radius:3px!important;color:var(--ink)!important;font-size:.95rem!important;line-height:1.85!important;padding:20px!important;}
#sources-box textarea{background:var(--warm)!important;border:1px solid var(--border)!important;border-left:3px solid var(--sage)!important;border-radius:3px!important;color:var(--sage)!important;font-size:.85rem!important;line-height:1.8!important;}
#chunks-box textarea{background:var(--warm)!important;border:1px solid var(--border)!important;border-radius:3px!important;color:var(--slate)!important;font-size:.8rem!important;line-height:1.7!important;}
.gr-accordion>.label-wrap{background:var(--warm)!important;border:1px solid var(--border)!important;border-radius:3px!important;color:var(--muted)!important;font-family:'Outfit',sans-serif!important;font-size:.7rem!important;font-weight:600!important;letter-spacing:.12em!important;text-transform:uppercase!important;}
.gr-accordion>.label-wrap:hover{border-color:var(--gold)!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:var(--warm);}::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}::-webkit-scrollbar-thumb:hover{background:var(--gold);}
"""

HEADER = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Outfit:wght@300;400;500;600&display=swap');
#gr-hdr{border-bottom:1px solid #e2ddd5;padding:44px 0 0;text-align:center;}
#gr-hdr .eye{font:600 9px/1 'Outfit',sans-serif;letter-spacing:.22em;text-transform:uppercase;color:#c9a84c;display:flex;align-items:center;justify-content:center;gap:12px;margin-bottom:14px;}
#gr-hdr .eye::before,#gr-hdr .eye::after{content:'';display:inline-block;width:36px;height:1px;background:#c9a84c;}
#gr-hdr h1{font:700 clamp(1.8rem,4vw,3rem)/1.08 'Playfair Display',serif;color:#0f0e17;margin:0 0 8px;}
#gr-hdr h1 em{font-style:italic;color:#c9a84c;}
#gr-hdr .sub{font:300 .88rem/1.7 'Outfit',sans-serif;color:#9a9080;margin:0 auto 6px;max-width:440px;}
#gr-hdr .dash-link{display:inline-block;margin-bottom:20px;font:600 9px/1 'Outfit',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#c9a84c;text-decoration:none;border-bottom:1px solid #c9a84c44;padding-bottom:2px;transition:border-color .2s;}
#gr-hdr .dash-link:hover{border-color:#c9a84c;}
#gr-hdr .stats{display:flex;border-top:1px solid #e2ddd5;}
#gr-hdr .s{flex:1;padding:12px 0;text-align:center;border-right:1px solid #e2ddd5;}
#gr-hdr .s:last-child{border-right:none;}
#gr-hdr .sn{font:700 1.4rem/1 'Playfair Display',serif;color:#0f0e17;display:block;}
#gr-hdr .sl{font:600 8px/1 'Outfit',sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#9a9080;display:block;margin-top:3px;}
</style>
<div id="gr-hdr">
  <div class="eye">Georgia State University &nbsp; CS Department</div>
  <h1>The <em>Unofficial</em> Professor Guide</h1>
  <p class="sub">Ask any question — answers are grounded in real student reviews.</p>
  <a class="dash-link" href="http://localhost:5000" target="_blank">
    ↗ Open Interactive Dashboard (Battle Mode, Radar Charts, Leaderboard)
  </a>
  <div class="stats">
    <div class="s"><span class="sn">12</span><span class="sl">Professors</span></div>
    <div class="s"><span class="sn">100+</span><span class="sl">Reviews</span></div>
    <div class="s"><span class="sn" id="gr-qct">0</span><span class="sl">Questions asked</span></div>
  </div>
</div>
"""

HOW_IT_WORKS = """
<style>
#gr-how{padding:18px 0 4px;}
#gr-how .title{font:600 8px/1 'Outfit',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#9a9080;display:flex;align-items:center;gap:8px;margin-bottom:12px;}
#gr-how .title::after{content:'';flex:1;height:1px;background:#e2ddd5;}
#gr-how .steps{display:flex;border:1px solid #e2ddd5;border-radius:3px;overflow:hidden;}
#gr-how .step{flex:1;padding:12px 8px;text-align:center;border-right:1px solid #e2ddd5;cursor:default;transition:background .2s;}
#gr-how .step:last-child{border-right:none;}
#gr-how .step:hover{background:#f5f0e8;}
#gr-how .num{width:22px;height:22px;border-radius:50%;background:#0f0e17;color:#c9a84c;font:600 8px/22px 'Outfit',sans-serif;text-align:center;margin:0 auto 7px;display:block;}
#gr-how .lbl{font:600 9px/1.3 'Outfit',sans-serif;color:#0f0e17;}
#gr-how .dsc{font:300 8px/1.4 'Outfit',sans-serif;color:#9a9080;margin-top:2px;}
</style>
<div id="gr-how">
  <div class="title">How it works</div>
  <div class="steps">
    <div class="step"><span class="num">01</span><div class="lbl">You ask</div><div class="dsc">Type any question</div></div>
    <div class="step"><span class="num">02</span><div class="lbl">Retrieve</div><div class="dsc">Top-5 review chunks via ChromaDB</div></div>
    <div class="step"><span class="num">03</span><div class="lbl">Generate</div><div class="dsc">Groq Llama 3.3 — context only</div></div>
    <div class="step"><span class="num">04</span><div class="lbl">Cite</div><div class="dsc">Source files attributed</div></div>
  </div>
</div>
"""

PROF_GRID = """
<style>
#gr-pg{padding:14px 0 6px;}
#gr-pg .title{font:600 8px/1 'Outfit',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#9a9080;display:flex;align-items:center;gap:8px;margin-bottom:10px;}
#gr-pg .title::after{content:'';flex:1;height:1px;background:#e2ddd5;}
#gr-pg .hint{font:300 8px/1 'Outfit',sans-serif;color:#bfb8ac;margin-top:8px;}
#gr-pg .grid{display:flex;flex-wrap:wrap;gap:5px;}
.gr-pill{display:flex;align-items:center;gap:6px;padding:4px 10px 4px 4px;background:#faf9f6;border:1px solid #e2ddd5;border-radius:3px;cursor:pointer;transition:border-color .15s,background .15s,transform .15s;user-select:none;}
.gr-pill:hover{border-color:#c9a84c;background:#fdf8ee;transform:translateY(-1px);}
.gr-av{width:20px;height:20px;border-radius:2px;background:#0f0e17;display:flex;align-items:center;justify-content:center;font:600 7px/1 'Outfit',sans-serif;color:#c9a84c;flex-shrink:0;}
.gr-pn{font:400 10px/1 'Outfit',sans-serif;color:#5a6a7a;}
</style>
<div id="gr-pg">
  <div class="title">Click a professor to ask about them</div>
  <div class="grid" id="gr-prof-grid"></div>
  <div class="hint">↑ Click any card to instantly pre-fill a question</div>
</div>
<script>
(function(){
  var profs=[
    {name:"Mohammed Alser",init:"MA",q:"What do students say about Mohammed Alser's grading and teaching style?"},
    {name:"Ashwin Ashok",init:"AA",q:"What is Ashwin Ashok known for according to student reviews?"},
    {name:"Bal Abdullah",init:"BA",q:"Does Bal Abdullah require attendance according to student reviews?"},
    {name:"Xie Bingyi",init:"XB",q:"What do students say about Xie Bingyi?"},
    {name:"Esra Akbas",init:"EA",q:"What is Esra Akbas like as a professor?"},
    {name:"S M Islam",init:"SI",q:"Which professor for CSC 2720 is most frequently described as explaining concepts clearly?"},
    {name:"William Johnson",init:"WJ",q:"What makes William Johnson stand out according to student reviews?"},
    {name:"Gao Lan",init:"GL",q:"What do students say about Gao Lan's exams and workload?"},
    {name:"Mufzur Rahaman",init:"MR",q:"What is Mufzur Rahaman like as a professor?"},
    {name:"Tushara Sadasivuni",init:"TS",q:"Is Tushara Sadasivuni's workload heavy according to student reviews?"},
    {name:"Saliesh Kumar",init:"SK",q:"What do students say about Saliesh Kumar?"},
    {name:"Hosseini Roya",init:"HR",q:"What are student reviews of Hosseini Roya like?"},
  ];
  var grid=document.getElementById("gr-prof-grid");
  profs.forEach(function(p){
    var pill=document.createElement("div");
    pill.className="gr-pill";
    pill.innerHTML='<div class="gr-av">'+p.init+'</div><span class="gr-pn">'+p.name+'</span>';
    pill.onclick=function(){
      var ta=document.querySelector("#question-box textarea");
      if(ta){
        var nv=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value");
        nv.set.call(ta,p.q);
        ta.dispatchEvent(new Event("input",{bubbles:true}));
        ta.focus();
        ta.scrollIntoView({behavior:"smooth",block:"center"});
      }
    };
    grid.appendChild(pill);
  });
})();
</script>
"""

HISTORY = """
<style>
#gr-hist{padding:10px 0 0;}
#gr-hist .title{font:600 8px/1 'Outfit',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#9a9080;display:flex;align-items:center;gap:8px;margin-bottom:8px;}
#gr-hist .title::after{content:'';flex:1;height:1px;background:#e2ddd5;}
#gr-hist .list{display:flex;flex-direction:column;gap:4px;}
.hist-item{display:flex;align-items:center;gap:7px;padding:6px 10px;background:#faf9f6;border:1px solid #e2ddd5;border-radius:3px;cursor:pointer;transition:border-color .15s,background .15s;}
.hist-item:hover{border-color:#c9a84c;background:#fdf8ee;}
.hist-icon{color:#c9a84c;font-size:11px;flex-shrink:0;}
.hist-text{font:300 .78rem/1.3 'Outfit',sans-serif;color:#5a6a7a;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;}
</style>
<div id="gr-hist">
  <div class="title">Recent questions</div>
  <div class="list" id="gr-hist-list">
    <div style="font:300 italic 9px/1 'Outfit',sans-serif;color:#bfb8ac;padding:2px 0;">Your questions will appear here</div>
  </div>
</div>
<script>
window._grAddHistory=function(q){
  var list=document.getElementById("gr-hist-list");
  if(!list)return;
  var empties=list.querySelectorAll("div");
  empties.forEach(function(e){if(e.style.fontStyle==='italic'||e.textContent.includes('appear here'))e.remove();});
  var item=document.createElement("div");
  item.className="hist-item";
  item.innerHTML='<span class="hist-icon">↵</span><span class="hist-text">'+q+'</span>';
  item.onclick=function(){
    var ta=document.querySelector("#question-box textarea");
    if(ta){
      var nv=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value");
      nv.set.call(ta,q);
      ta.dispatchEvent(new Event("input",{bubbles:true}));
    }
  };
  list.insertBefore(item,list.firstChild);
  if(list.children.length>5)list.removeChild(list.lastChild);
};
</script>
"""

ORNAMENT = '<div style="text-align:center;color:#e2ddd5;font-size:13px;letter-spacing:.5em;padding:10px 0;user-select:none;">✦ &nbsp; ✦ &nbsp; ✦</div>'
ANS_LBL  = '<div style="font:600 8px/1 \'Outfit\',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#c9a84c;margin:16px 0 5px 2px;">■ &nbsp; Answer</div>'
SRC_LBL  = '<div style="font:600 8px/1 \'Outfit\',sans-serif;letter-spacing:.2em;text-transform:uppercase;color:#4a7c59;margin:14px 0 5px 2px;">■ &nbsp; Sources retrieved</div>'

FOOTER_JS = """
<style>
#gr-ftr{text-align:center;padding:22px 0 8px;border-top:1px solid #e2ddd5;margin-top:10px;font:400 8px/1 'Outfit',sans-serif;letter-spacing:.1em;color:#9a9080;}
#gr-toast{position:fixed;bottom:24px;right:24px;z-index:999;background:#0f0e17;color:#c9a84c;border-radius:3px;font:600 10px/1 'Outfit',sans-serif;letter-spacing:.08em;padding:10px 18px;opacity:0;transform:translateY(8px);transition:opacity .25s,transform .25s;pointer-events:none;}
#gr-toast.show{opacity:1;transform:translateY(0);}
</style>
<div id="gr-ftr">ChromaDB &nbsp;·&nbsp; all-MiniLM-L6-v2 &nbsp;·&nbsp; Groq Llama 3.3 &nbsp;·&nbsp; Gradio + Flask</div>
<div id="gr-toast"></div>
<script>
window._grToast=function(msg){
  var t=document.getElementById("gr-toast");
  if(!t)return; t.textContent=msg; t.classList.add("show");
  setTimeout(function(){t.classList.remove("show");},2200);
};
var _grQc=0;
window._grTick=function(q){
  _grQc++;
  var el=document.getElementById("gr-qct");
  if(el)el.textContent=_grQc;
  if(window._grAddHistory)window._grAddHistory(q);
  window._grToast("Searching reviews…");
};
/* typewriter */
(function(){
  var phrases=["Which professor explains concepts most clearly?","Who is the most lenient grader?","Which professor has the heaviest workload?","Who requires attendance every class?","Whose exams are based on lecture slides?","Who has the best overall student reviews?"];
  var pi=0,ci=0,del=false;
  function tick(){
    var ta=document.querySelector("#question-box textarea");
    if(!ta||document.activeElement===ta){setTimeout(tick,200);return;}
    var ph=phrases[pi];
    if(!del){ta.placeholder=ph.slice(0,ci+1);ci++;if(ci===ph.length){del=true;setTimeout(tick,2000);return;}setTimeout(tick,52);}
    else{ta.placeholder=ph.slice(0,ci-1);ci--;if(ci===0){del=false;pi=(pi+1)%phrases.length;setTimeout(tick,400);return;}setTimeout(tick,22);}
  }
  setTimeout(tick,1400);
})();
</script>
"""

FAQ_SECTION = """
<style>
#gr-faq { padding: 12px 0 4px; }
#gr-faq .faq-title {
    font:600 8px/1 'Outfit',sans-serif; letter-spacing:.2em; text-transform:uppercase;
    color:#9a9080; display:flex; align-items:center; gap:10px; margin-bottom:12px;
}
#gr-faq .faq-title::after { content:''; flex:1; height:1px; background:#e2ddd5; }
#gr-faq .faq-card {
    display:flex; align-items:center; gap:14px;
    padding:12px 16px; margin-bottom:7px;
    background:#fff; border:1px solid #e2ddd5; border-radius:3px;
    cursor:pointer; transition:border-color .18s, background .18s, transform .12s;
}
#gr-faq .faq-card:hover {
    border-color:#c9a84c; background:#fdf8ee; transform:translateX(3px);
}
#gr-faq .faq-num {
    font:700 1.1rem/1 'Playfair Display',serif; color:#e2ddd5;
    flex-shrink:0; width:24px;
}
#gr-faq .faq-body { flex:1; }
#gr-faq .faq-q {
    font:400 .88rem/1.4 'Outfit',sans-serif; color:#0f0e17;
}
#gr-faq .faq-tag {
    font:600 8px/1 'Outfit',sans-serif; letter-spacing:.1em;
    text-transform:uppercase; color:#9a9080; margin-top:4px;
}
#gr-faq .faq-arrow {
    font:600 9px/1 'Outfit',sans-serif; letter-spacing:.1em;
    text-transform:uppercase; color:#c9a84c; flex-shrink:0;
}
</style>
<div id="gr-faq">
  <div class="faq-title">Frequently asked questions</div>

  <div class="faq-card" onclick="setQ('Which professor for CSC 2720 is most frequently described as explaining concepts clearly?')">
    <span class="faq-num">01</span>
    <div class="faq-body">
      <div class="faq-q">Which professor for CSC 2720 is most frequently described as explaining concepts clearly?</div>
      <div class="faq-tag">Course · CSC 2720</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

  <div class="faq-card" onclick="setQ('Which professor requires attendance according to student reviews?')">
    <span class="faq-num">02</span>
    <div class="faq-body">
      <div class="faq-q">Which professor requires attendance according to student reviews?</div>
      <div class="faq-tag">Policy · Attendance</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

  <div class="faq-card" onclick="setQ('Which professor is described as having a heavy workload?')">
    <span class="faq-num">03</span>
    <div class="faq-body">
      <div class="faq-q">Which professor is described as having a heavy workload?</div>
      <div class="faq-tag">Workload · Difficulty</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

  <div class="faq-card" onclick="setQ('Which professor is lenient in grading?')">
    <span class="faq-num">04</span>
    <div class="faq-body">
      <div class="faq-q">Which professor is lenient in grading?</div>
      <div class="faq-tag">Grading · Policy</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

  <div class="faq-card" onclick="setQ('Which professor has the best reviews irrespective of the course?')">
    <span class="faq-num">05</span>
    <div class="faq-body">
      <div class="faq-q">Which professor has the best reviews irrespective of the course?</div>
      <div class="faq-tag">Overall · Rating</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

  <div class="faq-card" onclick="setQ(&quot;Which professor\\'s exams are primarily based on lecture slides?&quot;)">
    <span class="faq-num">06</span>
    <div class="faq-body">
      <div class="faq-q">Which professor's exams are primarily based on lecture slides?</div>
      <div class="faq-tag">Exams · Study Tips</div>
    </div>
    <span class="faq-arrow">Ask →</span>
  </div>

</div>
<script>
function setQ(q) {
  var ta = document.querySelector("#question-box textarea");
  if (!ta) return;
  var nv = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value");
  nv.set.call(ta, q);
  ta.dispatchEvent(new Event("input", { bubbles: true }));
  ta.focus();
  ta.scrollIntoView({ behavior: "smooth", block: "center" });
}
</script>
"""

EXAMPLES = [
    ["Which professor for CSC 2720 is most frequently described as explaining concepts clearly?"],
    ["Which professor requires attendance according to student reviews?"],
    ["Which professor is described as having a heavy workload?"],
    ["Which professor is lenient in grading?"],
    ["Which professor has the best reviews irrespective of the course?"],
    ["Which professor's exams are primarily based on lecture slides?"],
]

def handle_query(question: str, professor: str = ""):
    question = question.strip()
    if not question:
        return "Please enter a question.", "", ""
    prof_filter = professor if professor else None
    result  = ask(question, professor=prof_filter)
    answer  = result["answer"]
    if prof_filter:
        answer += f"\n\n[Metadata filter active: only {professor}.txt was searched]"
    sources = "\n".join(
        f"• {s.replace('prof_','').replace('.txt','')}"
        for s in result["sources"]
    )
    chunks_detail = ""
    for i, c in enumerate(result["chunks"], 1):
        name = c["source"].replace("prof_","").replace(".txt","")
        chunks_detail += f"[{i}] {name}  —  distance: {c['distance']:.4f}\n{c['text'][:300]}\n\n"
    return answer, sources, chunks_detail.strip()

with gr.Blocks(title="GSU CS — AI Chat") as gradio_app:
    gr.HTML(HEADER)
    gr.HTML(HOW_IT_WORKS)

    question_box = gr.Textbox(
        label="Your question",
        placeholder="Which professor explains concepts most clearly?",
        lines=2, elem_id="question-box",
    )
    professor_filter = gr.Dropdown(
        choices=[
            ("No filter — search all professors", ""),
            ("Mohammed Alser",     "prof_Alser"),
            ("Ashwin Ashok",       "prof_Ashok"),
            ("Bal Abdullah",       "prof_Bal"),
            ("Xie Bingyi",         "prof_Bingyi"),
            ("Esra Akbas",         "prof_Esra"),
            ("S M Islam",          "prof_Islam"),
            ("William Johnson",    "prof_Johnson"),
            ("Gao Lan",            "prof_Lan"),
            ("Mahfuzur Rahman",    "prof_Rahman"),
            ("Tushara Sadasivuni", "prof_Sadasivuni"),
            ("Saliesh Kumar",      "prof_Kumar"),
            ("Hosseini Roya",      "prof_Roya"),
        ],
        value="",
        label="Filter by professor (metadata filter — restricts retrieval to one professor's reviews)",
        elem_id="prof-filter",
    )
    ask_btn = gr.Button("Ask →", elem_id="ask-btn")

    gr.HTML(FAQ_SECTION)
    gr.HTML(PROF_GRID)
    gr.HTML(HISTORY)
    gr.HTML(ORNAMENT)
    gr.HTML(ANS_LBL)

    answer_box = gr.Textbox(label="", lines=8, interactive=False, elem_id="answer-box")
    gr.HTML(SRC_LBL)
    sources_box = gr.Textbox(label="", lines=3, interactive=False, elem_id="sources-box")

    with gr.Accordion("Retrieved chunks — inspection & evaluation", open=False):
        chunks_box = gr.Textbox(label="", lines=14, interactive=False, elem_id="chunks-box")

    gr.HTML(FOOTER_JS)

    def wrapped(question, professor):
        return handle_query(question, professor)

    ask_btn.click(
        fn=wrapped, inputs=[question_box, professor_filter],
        outputs=[answer_box, sources_box, chunks_box],
        js="(q, p) => { window._grTick && window._grTick(q); return [q, p]; }",
    )
    question_box.submit(
        fn=wrapped, inputs=[question_box, professor_filter],
        outputs=[answer_box, sources_box, chunks_box],
        js="(q, p) => { window._grTick && window._grTick(q); return [q, p]; }",
    )

def run_gradio():
    print("  AI Chat     → http://localhost:7860")
    gradio_app.launch(server_port=7860, css=CSS)

# ═══════════════════════════════════════════════════════════════════
# LAUNCHER — both servers in parallel threads
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "="*52)
    print("  GSU CS Unofficial Professor Guide")
    print("="*52)
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    run_gradio()   # Gradio runs on main thread (required)