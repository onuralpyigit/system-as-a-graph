import { expect, test } from "@playwright/test";

test("home page renders the Operations Panel placeholder", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "System as a Graph — Operations Panel" })
  ).toBeVisible();
});
