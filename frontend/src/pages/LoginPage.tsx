import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { z } from "zod";
import { login } from "../services/auth";

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    await login(values.email, values.password);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
    navigate("/");
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="mx-auto max-w-md space-y-4 rounded-3xl bg-white p-6">
      <h1 className="text-4xl">Sign in</h1>
      <label className="block text-sm">
        Email
        <input className="mt-1 w-full rounded-xl border border-line px-3 py-2" {...form.register("email")} />
      </label>
      <label className="block text-sm">
        Password
        <input type="password" className="mt-1 w-full rounded-xl border border-line px-3 py-2" {...form.register("password")} />
      </label>
      {form.formState.errors.password ? <p className="text-sm text-clay">Use at least 8 characters.</p> : null}
      <button type="submit" className="rounded-full bg-ink px-5 py-3 text-paper">
        Sign in
      </button>
      <p className="text-sm">
        New here? <Link to="/register">Create an account</Link>
      </p>
    </form>
  );
}
