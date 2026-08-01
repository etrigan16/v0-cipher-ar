import { describe, expect, it } from "vitest"
import { cn } from "@/lib/utils"

describe("cn", () => {
  it("joins truthy class names with a space", () => {
    expect(cn("a", "b")).toBe("a b")
  })

  it("filters out falsy values", () => {
    expect(cn("a", false, null, undefined, 0, "b")).toBe("a b")
  })

  it("merges conflicting Tailwind classes keeping the last one", () => {
    expect(cn("p-2", "p-4")).toBe("p-4")
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500")
  })

  it("keeps non-conflicting classes intact", () => {
    expect(cn("p-4", "text-sm", "font-mono")).toBe("p-4 text-sm font-mono")
  })
})
