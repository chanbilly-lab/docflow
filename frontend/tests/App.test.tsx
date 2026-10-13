import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import App from "../src/App";
import { decide, filterCases, initialCases } from "../src/demo";

describe("application shell", () => {
  it("renders the review workspace with an explicit local demo boundary", () => {
    const html = renderToStaticMarkup(<App />);
    expect(html).toContain('id="workspace"');
    expect(html).toContain("讓審核，井然有序。");
    expect(html).toContain("本機示範");
    expect(html).toContain("資料不會上傳");
    expect(html).toContain("青嶼設計有限公司");
    expect(html).toContain('aria-label="搜尋案件"');
  });
  it("combines company, owner or ID search with status filtering", () => {
    const cases = initialCases();
    expect(
      filterCases(cases, "  df-0248  ", "ALL").map((item) => item.id),
    ).toEqual(["DF-0248"]);
    expect(filterCases(cases, "陳思穎", "IN_REVIEW")).toHaveLength(1);
    expect(filterCases(cases, "青嶼", "APPROVED")).toEqual([]);
    expect(filterCases(cases, "沒有這家公司", "ALL")).toEqual([]);
  });
  it("requires a started review and all required checks before approval", () => {
    const item = initialCases()[0];
    expect(() => decide(item, "APPROVED", "")).toThrow("請先領取");
    expect(() =>
      decide({ ...item, status: "IN_REVIEW" }, "APPROVED", ""),
    ).toThrow("必要檢查");
    expect(() =>
      decide({ ...item, status: "IN_REVIEW", checks: [] }, "APPROVED", ""),
    ).toThrow("必要檢查");
  });
  it.each(["REJECTED", "NEEDS_INFORMATION"] as const)(
    "requires a reason for %s",
    (decision) => {
      const item = initialCases()[1];
      expect(() => decide(item, decision, "   ")).toThrow("請填寫原因");
      const next = decide(item, decision, "  請提供清晰的地址證明  ");
      expect(next.status).toBe(decision);
      expect(next.history.at(-1)?.detail).toBe("請提供清晰的地址證明");
      expect(item.status).toBe("IN_REVIEW");
    },
  );
  it("keeps prior history immutable and rejects a second terminal decision", () => {
    const item = { ...initialCases()[1], checks: [true, true, true, true] };
    const next = decide(item, "APPROVED", "");
    expect(next.history).toHaveLength(item.history.length + 1);
    expect(next.history.slice(0, -1)).toEqual(item.history);
    expect(() => decide(next, "REJECTED", "changed")).toThrow("請先領取");
    expect(initialCases()[1].checks).toEqual([false, false, false, false]);
  });
});
