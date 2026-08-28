import { Link } from "react-router-dom";
import {
  FileText,
  Quote,
  Search,
  Sparkles,
  ShieldCheck,
  Layers,
} from "lucide-react";

const features = [
  {
    icon: <FileText size={19} />,
    title: "Upload your corpus",
    desc: "Drop in PDFs — papers, reports, theses — and ResearchLens indexes every page for retrieval.",
  },
  {
    icon: <Search size={19} />,
    title: "Ask in plain language",
    desc: "Query across an entire workspace at once instead of skimming documents one by one.",
  },
  {
    icon: <Quote size={19} />,
    title: "Answers with citations",
    desc: "Every response links back to the source document and page, so nothing is unverifiable.",
  },
  {
    icon: <Layers size={19} />,
    title: "Workspaces per project",
    desc: "Keep each literature review, client brief, or course isolated and tidy.",
  },
  {
    icon: <Sparkles size={19} />,
    title: "Persistent threads",
    desc: "Chat history is saved per workspace so you can pick a line of inquiry back up later.",
  },
  {
    icon: <ShieldCheck size={19} />,
    title: "Your account, your docs",
    desc: "Token-authenticated access with signed, short-lived document download links.",
  },
];

export default function Landing() {
  return (
    <>
      <section className="container hero">
        <span className="badge">
          <Sparkles size={13} /> Cited answers from your own documents
        </span>
        <h1 style={{ marginTop: 20 }}>
          Read less. <span>Understand more.</span>
        </h1>
        <p>
          ResearchLens turns a pile of PDFs into a searchable, conversational
          knowledge base — with every answer traced back to the exact page it
          came from.
        </p>
        <div className="hero-actions">
          <Link to="/auth?mode=register" className="btn btn-primary">
            Start free
          </Link>
          <Link to="/auth" className="btn btn-ghost">
            I already have an account
          </Link>
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>Built for people who read for a living</h2>
          <p>
            Everything you need to interrogate a document set, nothing you
            don't.
          </p>
        </div>
        <div className="grid-3">
          {features.map((f) => (
            <div className="card feature" key={f.title}>
              <div className="ico">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="container section">
        <div className="section-head">
          <h2>Three steps to your first answer</h2>
        </div>
        <div className="steps">
          {[
            [
              "Create a workspace",
              "Name it after your project and upload the PDFs that belong to it.",
            ],
            [
              "Let indexing finish",
              "We parse and embed each page — you'll see the progress live.",
            ],
            [
              "Ask anything",
              "Get a synthesized answer plus the page-level citations behind it.",
            ],
          ].map(([t, d], i) => (
            <div className="card step" key={t}>
              <span className="step-n">{i + 1}</span>
              <div>
                <h3 style={{ fontSize: 15, marginBottom: 5 }}>{t}</h3>
                <p className="muted" style={{ margin: 0, fontSize: 14 }}>
                  {d}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div style={{ textAlign: "center", marginTop: 34 }}>
          <Link to="/auth?mode=register" className="btn btn-primary">
            Create your first workspace
          </Link>
        </div>
      </section>

      <footer className="container footer">
        <span>© {new Date().getFullYear()} ResearchLens</span>
        <span>Answers you can check.</span>
      </footer>
    </>
  );
}
