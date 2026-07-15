"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { DAY_LABELS, MEAL_SLOTS, type MealPlan } from "@/lib/types";

function nextMonday(): string {
  const today = new Date();
  const day = today.getDay();
  const daysUntilMonday = day === 1 ? 7 : ((8 - day) % 7) || 7;
  const monday = new Date(today);
  monday.setDate(today.getDate() + daysUntilMonday);
  return monday.toISOString().slice(0, 10);
}

export default function PlanPage() {
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<MealPlan[]>("/meal-plans")
      .then((data) => {
        setPlans(data);
        setError(null);
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load meal plans"),
      )
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      await apiFetch<MealPlan>("/meal-plans", {
        method: "POST",
        body: JSON.stringify({ week_start_date: nextMonday() }),
      });
      const data = await apiFetch<MealPlan[]>("/meal-plans");
      setPlans(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate a meal plan");
    } finally {
      setGenerating(false);
    }
  }

  const currentPlan = plans[0];

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Your meal plan</h1>
        <Button onClick={handleGenerate} disabled={generating}>
          {generating ? "Generating..." : "Generate this week's plan"}
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {loading && <p className="text-sm text-muted-foreground">Loading...</p>}

      {!loading && !currentPlan && (
        <p className="text-sm text-muted-foreground">
          No meal plan yet - click &ldquo;Generate this week&apos;s plan&rdquo; to create one.
        </p>
      )}

      {currentPlan && (
        <>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">
              Week of {currentPlan.week_start_date}
            </span>
            <Badge variant="secondary">${currentPlan.total_cost.toFixed(2)} total</Badge>
            <Link
              href={`/plan/${currentPlan.id}/grocery-list`}
              className="text-sm underline"
            >
              View grocery list
            </Link>
          </div>

          <div className="grid gap-3 md:grid-cols-7">
            {DAY_LABELS.map((label, day) => (
              <Card key={day}>
                <CardHeader>
                  <CardTitle className="text-sm">{label}</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  {MEAL_SLOTS.map((slot) => {
                    const entry = currentPlan.entries.find(
                      (e) => e.day_of_week === day && e.meal_slot === slot,
                    );
                    return (
                      <div key={slot} className="text-xs">
                        <div className="font-medium capitalize">{slot}</div>
                        <div className="text-muted-foreground">
                          {entry ? `${entry.recipe_name} - $${entry.cost.toFixed(2)}` : "-"}
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
