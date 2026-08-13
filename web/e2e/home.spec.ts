import { expect, test } from "@playwright/test";

test("an unauthenticated operator is redirected to login", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText("SaaG", { exact: true })).toBeVisible();
});

test("the login screen rejects an empty submission", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Username is required")).toBeVisible();
  await expect(page.getByText("Password is required")).toBeVisible();
});
