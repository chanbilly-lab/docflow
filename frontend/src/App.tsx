import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  checkNames,
  decide,
  documentNames,
  filterCases,
  initialCases,
  statuses,
  type Case,
  type Decision,
  type Status,
} from "./demo";

type IconName =
  | "grid"
  | "folder"
  | "check"
  | "list"
  | "arrow"
  | "search"
  | "plus"
  | "close"
  | "file"
  | "clock"
  | "help"
  | "chevron"
  | "download";
function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    folder: (
      <path d="M3 7V5a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z" />
    ),
    check: <path d="m5 12 4 4L19 6" />,
    list: <path d="M9 5h12M9 12h12M9 19h12M3 5h1M3 12h1M3 19h1" />,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    search: (
      <>
        <circle cx="10.5" cy="10.5" r="6.5" />
        <path d="m16 16 5 5" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    file: (
      <>
        <path d="M14 3H5v18h14V8Z" />
        <path d="M14 3v5h5M8 12h8M8 16h6" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    help: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 4m0 3h.01" />
      </>
    ),
    chevron: <path d="m9 5 7 7-7 7" />,
    download: <path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5" />,
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name]}
    </svg>
  );
}
function Badge({ status }: { status: Status }) {
  return (
    <span className={`badge ${status.toLowerCase()}`}>
      <i />
      {statuses[status]}
    </span>
  );
}

export default function App() {
  const [cases, setCases] = useState(initialCases);
  const [view, setView] = useState("overview");
  const [filter, setFilter] = useState<Status | "ALL">("ALL");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState("DF-0248");
  const [detailTab, setDetailTab] = useState("documents");
  const [modal, setModal] = useState<
    "create" | "help" | "templates" | "decision" | "document" | null
  >(null);
  const [decision, setDecision] = useState<Decision>("APPROVED");
  const [documentIndex, setDocumentIndex] = useState(0);
  const [notice, setNotice] = useState("");
  const dialog = useRef<HTMLDialogElement>(null);
  const detailPanel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!notice || modal) return;
    const timer = window.setTimeout(() => setNotice(""), 6000);
    return () => window.clearTimeout(timer);
  }, [notice, modal]);
  const active = cases.find((item) => item.id === selected);
  const visible = filterCases(cases, query, filter).filter(
    (item) =>
      view !== "review" ||
      ["REVIEW_PENDING", "IN_REVIEW"].includes(item.status),
  );
  const pending = cases.filter((item) =>
    ["REVIEW_PENDING", "IN_REVIEW"].includes(item.status),
  ).length;
  const waiting = cases.filter(
    (item) => item.status === "NEEDS_INFORMATION",
  ).length;
  const approved = cases.filter((item) => item.status === "APPROVED").length;
  const completed = cases.filter((item) =>
    ["APPROVED", "REJECTED"].includes(item.status),
  ).length;
  function openModal(next: typeof modal) {
    setNotice("");
    setModal(next);
    dialog.current?.showModal();
  }
  function closeModal() {
    dialog.current?.close();
    setModal(null);
  }
  function navigate(next: string) {
    setView(next);
    setFilter("ALL");
    setQuery("");
  }
  function update(next: Case) {
    setCases((items) =>
      items.map((item) => (item.id === next.id ? next : item)),
    );
  }
  function selectCase(id: string, reveal = false) {
    setSelected(id);
    setDetailTab("documents");
    if (reveal && window.matchMedia("(max-width: 1000px)").matches) {
      detailPanel.current?.scrollIntoView({ block: "start" });
      detailPanel.current?.focus({ preventScroll: true });
    }
  }
  function startReview() {
    if (!active || active.status !== "REVIEW_PENDING") return;
    update({
      ...active,
      status: "IN_REVIEW",
      history: [
        ...active.history,
        { title: "已領取並開始審核", detail: "示範審核者 · 本次操作" },
      ],
    });
    setDetailTab("checklist");
    setNotice("已開始本機示範審核，請完成必要檢查。");
  }
  function submitCase(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get("company") || "").trim(),
      owner = String(data.get("owner") || "").trim();
    if (!name || !owner) {
      setNotice("請填寫公司名稱與申請人，不能只輸入空白。");
      return;
    }
    const id = `DF-DEMO-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
    const next: Case = {
      id,
      name,
      owner,
      initials: name[0],
      status: "DRAFT",
      date: "本次新增",
      documents: 0,
      checks: [false, false, false, false],
      history: [{ title: "案件已建立", detail: `${owner} · 本次操作` }],
    };
    setCases((items) => [next, ...items]);
    selectCase(id);
    navigate("cases");
    closeModal();
    setNotice("示範草稿已建立；重新整理頁面後會重設。");
  }
  function submitDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active) return;
    try {
      update(
        decide(
          active,
          decision,
          String(new FormData(event.currentTarget).get("reason") || ""),
        ),
      );
      closeModal();
      setDetailTab("activity");
      setNotice(`示範案件${statuses[decision]}，未寄出通知。`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "操作未完成。");
    }
  }
  function exportList() {
    const blob = new Blob(
      [
        JSON.stringify(
          visible.map(({ id, name, owner, status }) => ({
            id,
            name,
            owner,
            status: statuses[status],
            demo: true,
          })),
          null,
          2,
        ),
      ],
      { type: "application/json" },
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement("a");
    link.href = url;
    link.download = "docflow-demo-cases.json";
    link.click();
    URL.revokeObjectURL(url);
    setNotice("已匯出目前篩選的示範案件。");
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace">
        跳至工作區
      </a>
      <aside className="sidebar">
        <a
          className="brand"
          href="#workspace"
          onClick={() => navigate("overview")}
        >
          <span className="brand-mark">
            <Icon name="file" size={24} />
          </span>
          docflow<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">
          <span className="workspace-icon">D</span>
          <div>
            DocFlow 工作空間<small>文件審核與協作</small>
          </div>
        </div>
        <p className="nav-label">工作空間</p>
        <nav aria-label="主要導覽">
          {(
            [
              { id: "overview", icon: "grid", label: "工作總覽" },
              { id: "cases", icon: "folder", label: "案件管理" },
              { id: "review", icon: "check", label: "待辦審核" },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              aria-current={view === item.id ? "page" : undefined}
              onClick={() => navigate(item.id)}
            >
              <Icon name={item.icon} />
              {item.label}
              {item.id === "review" && (
                <span className="nav-count">{pending}</span>
              )}
            </button>
          ))}
          <button className="nav-item" onClick={() => openModal("templates")}>
            <Icon name="list" />
            檢查清單範本
          </button>
        </nav>
        <div className="sidebar-note">
          <span className="small-orbit">↗</span>
          <h3>讓每份文件，有跡可循。</h3>
          <p>
            從提交到決策，將每一步
            <br />
            整理成清晰的審核歷程。
          </p>
          <button onClick={() => openModal("help")}>
            探索示範流程 <Icon name="arrow" size={16} />
          </button>
        </div>
        <div className="sidebar-bottom">
          <button className="nav-item" onClick={() => openModal("help")}>
            <Icon name="help" />
            使用說明
          </button>
          <div className="profile">
            <span className="avatar">示</span>
            <div>
              示範工作空間<small>本機互動預覽</small>
            </div>
            <span className="online-dot" />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            工作空間 <Icon name="chevron" size={14} />
            <strong>
              {view === "overview"
                ? "工作總覽"
                : view === "cases"
                  ? "案件管理"
                  : "待辦審核"}
            </strong>
          </div>
          <span className="demo-label">
            <i />
            本機示範<span> · 資料不會上傳</span>
          </span>
        </header>
        <main id="workspace">
          <section className="page-heading">
            <div>
              <p className="eyebrow">YOUR DOCUMENTS, IN FLOW</p>
              <h1>
                {view === "overview"
                  ? "讓審核，井然有序。"
                  : view === "cases"
                    ? "每一件，都清楚掌握。"
                    : "專注下一個決定。"}
              </h1>
              <p>整理文件、掌握進度，讓每一次決策都有依據。</p>
            </div>
            <button className="primary" onClick={() => openModal("create")}>
              <Icon name="plus" size={18} />
              建立示範案件
            </button>
          </section>
          {view === "overview" && (
            <section className="overview-grid" aria-label="案件概覽">
              <div className="focus-card">
                <div>
                  <span className="focus-tag">
                    <i />
                    審核工作台
                  </span>
                  <h2>
                    好的流程，
                    <br />
                    從清晰的下一步開始。
                  </h2>
                  <p>
                    目前有 <strong>{pending} 件案件</strong>{" "}
                    等待你接手或繼續審核。
                  </p>
                  <button onClick={() => navigate("review")}>
                    前往待辦審核 <Icon name="arrow" size={18} />
                  </button>
                </div>
                <div className="flow-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <div className="paper paper-back" />
                  <div className="paper">
                    <div className="paper-icon">
                      <Icon name="file" size={27} />
                    </div>
                    <span />
                    <span />
                    <span className="short" />
                    <div className="paper-check">
                      <Icon name="check" size={22} />
                    </div>
                  </div>
                  <span className="spark spark-one">+</span>
                  <span className="spark spark-two">+</span>
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-top">
                  <span>待處理案件</span>
                  <span className="metric-icon">
                    <Icon name="clock" />
                  </span>
                </div>
                <strong className="metric-number">
                  {pending.toString().padStart(2, "0")}
                  <small>件</small>
                </strong>
                <div className="metric-foot">
                  <span className="accent-dot" />
                  包含待審核與審核中
                </div>
              </div>
              <div className="metric-card">
                <div className="metric-top">
                  <span>已完成案件</span>
                  <span className="metric-icon sage">
                    <Icon name="check" />
                  </span>
                </div>
                <strong className="metric-number">
                  {completed.toString().padStart(2, "0")}
                  <small>件</small>
                </strong>
                <div className="progress-track">
                  <span
                    style={{ width: `${(completed / cases.length) * 100}%` }}
                  />
                </div>
                <div className="metric-foot">
                  {approved} 件核准 <span>／ {cases.length} 件案件</span>
                </div>
              </div>
            </section>
          )}
          <div className="section-heading">
            <div>
              <h2>
                {view === "review" ? "待辦審核" : "案件一覽"}
                <span className="total-count">
                  {view === "review" ? pending : cases.length}
                </span>
              </h2>
              <p>
                {view === "review"
                  ? "領取案件，依清單逐項完成審核。"
                  : "每一份申請，都有清楚的下一步。"}
              </p>
            </div>
            <button className="subtle-button" onClick={exportList}>
              <Icon name="download" size={16} />
              匯出清單
            </button>
          </div>
          <div className="work-grid">
            <section className="case-panel" aria-label="案件清單">
              <div className="list-toolbar">
                <label className="search-box">
                  <Icon name="search" size={18} />
                  <input
                    aria-label="搜尋案件"
                    placeholder="搜尋案件、公司或申請人…"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                  {query && (
                    <button aria-label="清除搜尋" onClick={() => setQuery("")}>
                      <Icon name="close" size={15} />
                    </button>
                  )}
                </label>
                <select
                  aria-label="篩選案件狀態"
                  value={filter}
                  onChange={(event) =>
                    setFilter(event.target.value as Status | "ALL")
                  }
                >
                  <option value="ALL">全部狀態</option>
                  {Object.entries(statuses).map(([key, value]) => (
                    <option key={key} value={key}>
                      {value}
                    </option>
                  ))}
                </select>
              </div>
              <div className="quick-filters" aria-label="快速篩選">
                <button
                  aria-pressed={filter === "ALL"}
                  onClick={() => setFilter("ALL")}
                >
                  全部案件
                </button>
                <button
                  aria-pressed={filter === "REVIEW_PENDING"}
                  onClick={() => setFilter("REVIEW_PENDING")}
                >
                  待審核{" "}
                  <span>
                    {
                      cases.filter((item) => item.status === "REVIEW_PENDING")
                        .length
                    }
                  </span>
                </button>
                <button
                  aria-pressed={filter === "NEEDS_INFORMATION"}
                  onClick={() => setFilter("NEEDS_INFORMATION")}
                >
                  待補件 <span>{waiting}</span>
                </button>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>案件 / 申請人</th>
                      <th>狀態</th>
                      <th>文件</th>
                      <th>建立日期</th>
                      <th>
                        <span className="sr-only">詳情</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {visible.map((item, index) => (
                      <tr
                        key={item.id}
                        className={active?.id === item.id ? "selected-row" : ""}
                      >
                        <td>
                          <button
                            className="case-link"
                            aria-label={`查看 ${item.name}`}
                            onClick={() => selectCase(item.id, true)}
                          >
                            <span
                              className={`company-avatar tone-${index % 4}`}
                            >
                              {item.initials}
                            </span>
                            <span>
                              <strong>{item.name}</strong>
                              <small>
                                {item.id} <span>·</span> {item.owner}
                              </small>
                            </span>
                          </button>
                        </td>
                        <td>
                          <Badge status={item.status} />
                        </td>
                        <td>
                          <span
                            className={`document-count ${item.documents < 4 ? "incomplete" : ""}`}
                          >
                            <Icon name="file" size={14} />
                            {item.documents}/4
                          </span>
                        </td>
                        <td className="date-cell">{item.date}</td>
                        <td>
                          <button
                            className="row-open"
                            aria-label={`開啟 ${item.id} 詳情`}
                            onClick={() => selectCase(item.id, true)}
                          >
                            <Icon name="chevron" size={16} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {visible.length === 0 && (
                <div className="empty-state">
                  <Icon name="search" size={30} />
                  <h3>沒有符合條件的案件</h3>
                  <p>試試其他關鍵字，或清除目前的篩選。</p>
                  <button
                    className="subtle-button"
                    onClick={() => {
                      setQuery("");
                      setFilter("ALL");
                    }}
                  >
                    清除搜尋與篩選
                  </button>
                </div>
              )}
              <footer className="list-footer">
                <span>
                  顯示 {visible.length} 件{view === "review" ? "待辦" : "案件"}
                </span>
                <span>示範資料 · 2026 年 9 月</span>
              </footer>
            </section>
            <aside
              ref={detailPanel}
              tabIndex={-1}
              className="detail-panel"
              aria-label="案件詳情"
            >
              {active && (
                <>
                  <div className="detail-heading">
                    <span className="eyebrow">CASE DETAILS</span>
                    <span className="detail-id">{active.id}</span>
                  </div>
                  <h2>{active.name}</h2>
                  <div className="detail-meta">
                    <Badge status={active.status} />
                    <span>供應商入駐</span>
                  </div>
                  <div className="detail-facts">
                    <div>
                      <span>申請人</span>
                      <strong>{active.owner}</strong>
                    </div>
                    <div>
                      <span>檢查清單</span>
                      <strong>
                        供應商入駐 <small>v1</small>
                      </strong>
                    </div>
                  </div>
                  <div className="detail-tabs" aria-label="詳情分類">
                    {[
                      { id: "documents", label: "文件" },
                      { id: "checklist", label: "檢查清單" },
                      { id: "activity", label: "歷程" },
                    ].map((tab) => (
                      <button
                        key={tab.id}
                        aria-pressed={detailTab === tab.id}
                        onClick={() => setDetailTab(tab.id)}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                  <div className="detail-content">
                    {detailTab === "documents" ? (
                      <>
                        <div className="content-caption">
                          必要文件 <span>{active.documents} / 4 份</span>
                        </div>
                        <div className="document-list">
                          {documentNames.map((name, index) => (
                            <button
                              key={name}
                              className="document-row"
                              disabled={index >= active.documents}
                              onClick={() => {
                                setDocumentIndex(index);
                                openModal("document");
                              }}
                            >
                              <span className="file-symbol">
                                <Icon name="file" size={20} />
                              </span>
                              <span>
                                <strong>{name}</strong>
                                <small>
                                  {index < active.documents
                                    ? "PDF · 示範文件"
                                    : "尚未提供"}
                                </small>
                              </span>
                              {index < active.documents ? (
                                <span className="file-check">
                                  <Icon name="check" size={15} />
                                </span>
                              ) : (
                                <span className="missing-dot" />
                              )}
                            </button>
                          ))}
                        </div>
                        <div className="detail-tip">
                          <Icon name="help" size={16} />
                          <span>
                            文件為示範資訊，未連接檔案預覽或上傳服務。
                          </span>
                        </div>
                      </>
                    ) : detailTab === "checklist" ? (
                      <>
                        <div className="content-caption">
                          必要檢查{" "}
                          <span>
                            {active.checks.filter(Boolean).length} / 4 項
                          </span>
                        </div>
                        {checkNames.map((name, index) => (
                          <label className="check-row" key={name}>
                            <input
                              type="checkbox"
                              checked={active.checks[index]}
                              disabled={active.status !== "IN_REVIEW"}
                              onChange={(event) =>
                                update({
                                  ...active,
                                  checks: active.checks.map((value, n) =>
                                    n === index ? event.target.checked : value,
                                  ),
                                })
                              }
                            />
                            <span>
                              {name}
                              <small>必要檢查</small>
                            </span>
                          </label>
                        ))}
                        <p className="detail-tip">
                          {active.status === "IN_REVIEW"
                            ? "完成所有必要檢查後，即可核准此示範案件。"
                            : "領取並開始審核後，才能勾選檢查項目。"}
                        </p>
                      </>
                    ) : (
                      <ol className="timeline">
                        {active.history.map((event, index) => (
                          <li key={index}>
                            <strong>{event.title}</strong>
                            <span>{event.detail}</span>
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                  <div className="detail-actions">
                    {active.status === "REVIEW_PENDING" ? (
                      <button className="primary wide" onClick={startReview}>
                        領取並開始示範審核 <Icon name="arrow" size={17} />
                      </button>
                    ) : active.status === "IN_REVIEW" ? (
                      <>
                        <button
                          className="primary wide"
                          disabled={!active.checks.every(Boolean)}
                          onClick={() => {
                            setDecision("APPROVED");
                            openModal("decision");
                          }}
                        >
                          <Icon name="check" size={17} />
                          核准示範案件
                        </button>
                        <div className="secondary-actions">
                          <button
                            onClick={() => {
                              setDecision("NEEDS_INFORMATION");
                              openModal("decision");
                            }}
                          >
                            要求補件
                          </button>
                          <button
                            className="reject"
                            onClick={() => {
                              setDecision("REJECTED");
                              openModal("decision");
                            }}
                          >
                            拒絕案件
                          </button>
                        </div>
                      </>
                    ) : (
                      <p className="resolved-note">
                        {active.status === "DRAFT"
                          ? "示範草稿已儲存在本頁記憶體中。"
                          : active.status === "NEEDS_INFORMATION"
                            ? "等待申請人補充文件。"
                            : "本次審核已結束，可於歷程查看紀錄。"}
                      </p>
                    )}
                  </div>
                </>
              )}
            </aside>
          </div>
          <footer className="page-footer">
            <span>
              <span className="footer-dot" />
              清楚的流程，可信的決策。
            </span>
            <span>DocFlow / 文件審核工作空間</span>
          </footer>
          <div
            role="status"
            className={`toast ${notice && !modal ? "shown" : ""}`}
          >
            {!modal && notice}
          </div>
        </main>
      </div>
      <dialog
        ref={dialog}
        aria-labelledby="dialog-title"
        onCancel={() => setModal(null)}
        onClose={() => setModal(null)}
      >
        <div className="modal-header">
          <span className="eyebrow">DOCFLOW DEMO</span>
          <button aria-label="關閉視窗" onClick={closeModal}>
            <Icon name="close" />
          </button>
        </div>
        {modal === "create" && (
          <form onSubmit={submitCase}>
            <h2 id="dialog-title">建立新的示範案件</h2>
            <p>從一份供應商入駐申請開始。所有資料僅保留於本次頁面。</p>
            <label className="form-field">
              公司名稱
              <input
                name="company"
                placeholder="例如：青嶼設計有限公司"
                required
                maxLength={80}
                autoFocus
              />
            </label>
            <label className="form-field">
              申請人
              <input
                name="owner"
                placeholder="輸入申請人姓名"
                required
                maxLength={40}
              />
            </label>
            <div className="form-info">
              <Icon name="list" />
              供應商入駐 · 檢查清單 v1 · 4 份必要文件
            </div>
            {notice && (
              <p role="alert" className="error-text">
                {notice}
              </p>
            )}
            <button className="primary wide" type="submit">
              建立示範草稿 <Icon name="arrow" size={17} />
            </button>
          </form>
        )}
        {modal === "decision" && (
          <form onSubmit={submitDecision}>
            <h2 id="dialog-title">
              {decision === "APPROVED"
                ? "確認核准案件"
                : decision === "REJECTED"
                  ? "確認拒絕案件"
                  : "要求補充文件"}
            </h2>
            <p>{active?.name} · 此操作只更新本機示範，不寄出通知。</p>
            {decision !== "APPROVED" && (
              <label className="form-field">
                {decision === "NEEDS_INFORMATION"
                  ? "需補充內容與原因"
                  : "拒絕原因"}
                <textarea
                  name="reason"
                  required
                  maxLength={500}
                  rows={4}
                  autoFocus
                  placeholder="說明你的決定，讓下一步更清楚…"
                />
              </label>
            )}
            {notice && (
              <p role="alert" className="error-text">
                {notice}
              </p>
            )}
            <div className="modal-actions">
              <button
                type="button"
                className="subtle-button"
                onClick={closeModal}
              >
                返回案件
              </button>
              <button className="primary" type="submit">
                確認示範決定
              </button>
            </div>
          </form>
        )}
        {modal === "templates" && (
          <>
            <h2 id="dialog-title">一致的標準，清晰的審核。</h2>
            <p>
              供應商入駐檢查清單 <span className="template-version">v1</span>
            </p>
            <ol className="template-list">
              {checkNames.map((name) => (
                <li key={name}>
                  {name}
                  <span>必要</span>
                </li>
              ))}
              <li>
                其他註冊資料觀察<span>選填</span>
              </li>
            </ol>
            <p className="modal-footnote">
              此頁展示範本內容，範本編輯與版本發布尚未串接。
            </p>
          </>
        )}
        {modal === "document" && (
          <>
            <h2 id="dialog-title">{documentNames[documentIndex]}</h2>
            <div className="document-preview">
              <Icon name="file" size={54} />
              <strong>示範文件資訊</strong>
              <p>
                這裡沒有實際 PDF 檔案。
                <br />
                正式文件預覽將在服務串接後提供。
              </p>
            </div>
            <p className="modal-footnote">所屬案件：{active?.name}</p>
          </>
        )}
        {modal === "help" && (
          <>
            <h2 id="dialog-title">從文件，到決策。</h2>
            <p>
              這是 DocFlow
              的本機互動示範，使用合成案件。操作不會上傳資料，也不會寄出郵件。
            </p>
            <ol className="help-steps">
              <li>搜尋或篩選案件，查看文件與歷程。</li>
              <li>選擇待審核案件，領取並開始示範審核。</li>
              <li>勾選必要檢查，再核准、拒絕或要求補件。</li>
            </ol>
            <p>重新整理頁面將清除變更；登入、實際上傳與雲端審核尚未串接。</p>
            <button
              className="subtle-button"
              onClick={() => {
                setCases(initialCases());
                selectCase("DF-0248");
                navigate("overview");
                closeModal();
                setNotice("已恢復初始示範資料。");
              }}
            >
              重設示範資料
            </button>
          </>
        )}
      </dialog>
    </div>
  );
}
