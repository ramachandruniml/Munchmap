import Link from "next/link";
import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6 text-center">
      <h1 className="text-4xl font-semibold tracking-tight">Munchmap</h1>
      <p className="max-w-md text-muted-foreground">
        Constraint-based weekly meal planning for college students - optimized for your budget,
        diet, and dorm equipment.
      </p>
      <div className="flex gap-3">
        <Link href="/signup" className={buttonVariants({ variant: "default" })}>
          Get started
        </Link>
        <Link href="/login" className={buttonVariants({ variant: "outline" })}>
          Log in
        </Link>
      </div>
    </div>
  );
}
