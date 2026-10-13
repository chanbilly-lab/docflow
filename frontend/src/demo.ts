export const statuses = {
  DRAFT: "草稿",
  REVIEW_PENDING: "待審核",
  IN_REVIEW: "審核中",
  NEEDS_INFORMATION: "待補件",
  APPROVED: "已核准",
  REJECTED: "已拒絕",
} as const;
export type Status = keyof typeof statuses;
export type Decision = "APPROVED" | "REJECTED" | "NEEDS_INFORMATION";
export type Case = {
  id: string;
  name: string;
  initials: string;
  owner: string;
  status: Status;
  date: string;
  documents: number;
  checks: boolean[];
  history: { title: string; detail: string }[];
};
export const documentNames = [
  "公司註冊證明",
  "董事身分證明",
  "銀行帳戶資料",
  "地址證明",
];
export const checkNames = [
  "公司名稱與註冊資料一致",
  "董事身分證明清晰且有效",
  "銀行受益人與申請公司一致",
  "地址證明與申請資料一致",
];
export function initialCases(): Case[] {
  return [
    ["0248", "青嶼設計有限公司", "青", "林以安", "REVIEW_PENDING", "09.29", 4],
    ["0247", "澄光科技有限公司", "澄", "陳思穎", "IN_REVIEW", "09.29", 4],
    [
      "0246",
      "山海物流有限公司",
      "山",
      "黃子謙",
      "NEEDS_INFORMATION",
      "09.28",
      3,
    ],
    ["0245", "森序生活有限公司", "森", "張雅晴", "APPROVED", "09.28", 4],
    ["0244", "禾日食品有限公司", "禾", "李承恩", "REVIEW_PENDING", "09.27", 4],
    ["0243", "島嶼文化有限公司", "島", "王亦文", "APPROVED", "09.27", 4],
    ["0242", "向野實業有限公司", "向", "周品言", "DRAFT", "09.26", 2],
    ["0241", "遠景貿易有限公司", "遠", "許庭軒", "REJECTED", "09.25", 4],
  ].map(([id, name, initials, owner, status, date, documents]) => ({
    id: `DF-${id}`,
    name: String(name),
    initials: String(initials),
    owner: String(owner),
    status: status as Status,
    date: String(date),
    documents: Number(documents),
    checks: Array<boolean>(4).fill(status === "APPROVED"),
    history: [
      { title: "案件已建立", detail: `${owner} · 2026.${date}` },
      ...(status === "DRAFT"
        ? []
        : [{ title: "文件已提交", detail: "申請人完成本次提交" }]),
      ...(status === "IN_REVIEW"
        ? [{ title: "審核已開始", detail: "示範審核者正在檢查文件" }]
        : status === "APPROVED"
          ? [{ title: "已核准", detail: "必要檢查已全部通過 · 示範紀錄" }]
          : status === "REJECTED"
            ? [{ title: "已拒絕", detail: "公司註冊資料不一致 · 示範紀錄" }]
            : status === "NEEDS_INFORMATION"
              ? [{ title: "待補件", detail: "請補充地址證明 · 示範紀錄" }]
              : []),
    ],
  }));
}
export function filterCases(
  cases: Case[],
  query: string,
  status: Status | "ALL",
) {
  const term = query.trim().toLocaleLowerCase();
  return cases.filter(
    (item) =>
      (status === "ALL" || item.status === status) &&
      `${item.id} ${item.name} ${item.owner}`
        .toLocaleLowerCase()
        .includes(term),
  );
}
export function decide(item: Case, decision: Decision, reason: string): Case {
  if (item.status !== "IN_REVIEW") throw new Error("請先領取並開始審核。");
  if (
    decision === "APPROVED" &&
    (item.checks.length !== checkNames.length || !item.checks.every(Boolean))
  )
    throw new Error("請先完成所有必要檢查。");
  if (decision !== "APPROVED" && !reason.trim())
    throw new Error("請填寫原因。");
  return {
    ...item,
    status: decision,
    history: [
      ...item.history,
      {
        title: statuses[decision],
        detail: reason.trim() || "示範審核者完成所有必要檢查",
      },
    ],
  };
}
