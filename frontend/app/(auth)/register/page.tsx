/**
 * app/(auth)/register/page.tsx
 *
 * Why this file exists:
 *   Registration form, mirroring login's structure. On success, logs the
 *   user straight in rather than making them re-enter credentials.
 */

"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import axios from "axios";
import { useAuthStore } from "@/store/authStore";

const registerSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const setTokens = useAuthStore((s) => s.setTokens);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterForm>({ resolver: zodResolver(registerSchema) });

  const onSubmit = async (values: RegisterForm) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
    try {
      await axios.post(`${baseUrl}/auth/register`, values);
      const { data } = await axios.post(`${baseUrl}/auth/login`, values);
      setTokens(data.access_token, data.refresh_token);
      router.push("/");
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.status === 409 ? "Email already registered" : "Registration failed";
      setError("root", { message });
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
        {isSubmitting ? "Creating account..." : "Create account"}
      </button>
      <p className="text-center text-sm text-text-muted">
        Already have an account? <a href="/login" className="text-accent hover:underline">Sign in</a>
      </p>
    </form>
  );
}
