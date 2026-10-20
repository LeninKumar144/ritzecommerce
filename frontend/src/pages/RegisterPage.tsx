import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { register as registerAccount } from "../services/auth";

const schema = z.object({
  full_name: z.string().min(1),
  email: z.string().email(),
  password: z.string().min(8),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    await registerAccount(values);
    await queryClient.invalidateQueries({ queryKey: ["me"] });
    navigate("/");
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="mx-auto max-w-md space-y-4 rounded-3xl bg-white p-6">
      <h1 className="text-4xl">Create account</h1>
      <label className="block text-sm">
        Name
        <input className="mt-1 w-full rounded-xl border border-line px-3 py-2" {...form.register("full_name")} />
      </label>
      <label className="block text-sm">
        Email
        <input className="mt-1 w-full rounded-xl border border-line px-3 py-2" {...form.register("email")} />
      </label>
      <label className="block text-sm">
        Password
        <input type="password" className="mt-1 w-full rounded-xl border border-line px-3 py-2" {...form.register("password")} />
      </label>
      <button type="submit" className="rounded-full bg-ink px-5 py-3 text-paper">
        Register
      </button>
    </form>
  );
}
