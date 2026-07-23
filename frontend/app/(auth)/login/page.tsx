/**
 * app/(auth)/login/page.tsx
 *
 * Why this file exists:
 *   Login form using React Hook Form + Zod, matching the spec's stated
 *   stack for form handling/validation. On success, stores tokens in
 *   authStore and redirects into the chat shell.
 */

"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { useAuthStore } from "@/store/authStore";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginForm) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
      const { data } = await axios.post(`${baseUrl}/auth/login`, values);
      setTokens(data.access_token, data.refresh_token);
      router.push("/");
    } catch {
      setError("root", { message: "Incorrect email or password" });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div>
        <label className="mb-1 block text-sm text-text-muted">Email</label>
        <input
          {...register("email")}
          type="email"
          className="w-full rounded-md border border-border bg-surface-raised px-3 py-2 text-text focus:outline-none"
        />
        {errors.email && <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>}
      </div>
      <div>
        <label className="mb-1 block text-sm text-text-muted">Password</label>
        <input
          {...register("password")}
          type="password"
          className="w-full rounded-md border border-border bg-surface-raised px-3 py-2 text-text focus:outline-none"
        />
        {errors.password && <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>}
      </div>
      {errors.root && <p className="text-sm text-red-400">{errors.root.message}</p>}
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-accent py-2 font-medium text-bg hover:bg-accent-hover disabled:opacity-50"
      >
        {isSubmitting ? "Signing in..." : "Sign in"}
      </button>
      <p className="text-center text-sm text-text-muted">
        No account? <a href="/register" className="text-accent hover:underline">Register</a>
      </p>
    </form>
  );
}
