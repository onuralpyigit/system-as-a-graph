"use client";

import { useLogin } from "@refinedev/core";
import { useForm } from "react-hook-form";
import { Waypoints } from "lucide-react";
import Image from "next/image";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface LoginFormValues {
  username: string;
  password: string;
}

export default function LoginPage() {
  const { mutate: login, data, isPending } = useLogin<LoginFormValues>();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>();

  const authFailed = data && !data.success;
  const errorMessage =
    authFailed && data.error instanceof Error ? data.error.message : "Auth failed — invalid credentials";

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-2">
      <div className="flex flex-col gap-4 p-6 md:p-10">
        <div className="flex items-center gap-2 text-sm font-medium">
          <div className="flex size-6 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Waypoints className="size-4" />
          </div>
          SaaG
        </div>
        <div className="flex flex-1 items-center justify-center">
          <div className="w-full max-w-xs">
            <form
              className="flex flex-col gap-6"
              onSubmit={handleSubmit((values) => login(values))}
            >
              <div className="flex flex-col items-center gap-1 text-center">
                <h1 className="text-2xl font-bold">Login to your account</h1>
                <p className="text-sm text-balance text-muted-foreground">
                  Enter your username and password to sign in
                </p>
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  autoComplete="username"
                  autoFocus
                  {...register("username", { required: true })}
                />
                {errors.username ? (
                  <span className="text-xs text-status-critical">Username is required</span>
                ) : null}
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register("password", { required: true })}
                />
                {errors.password ? (
                  <span className="text-xs text-status-critical">Password is required</span>
                ) : null}
              </div>

              {authFailed ? (
                <Alert variant="destructive">
                  <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
              ) : null}

              <Button type="submit" disabled={isPending} className="w-full">
                {isPending ? "Signing in…" : "Sign in"}
              </Button>
            </form>
          </div>
        </div>
      </div>
      <div className="relative hidden bg-muted lg:block">
        <Image src="/login-cover.jpg" alt="" fill priority className="object-cover" />
      </div>
    </div>
  );
}
