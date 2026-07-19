"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  const [ratings, setRatings] = useState<Record<number, boolean>>({});
  const [diningHallMeals, setDiningHallMeals] = useState("0");
  const [cookTimeMinutes, setCookTimeMinutes] = useState("");

  async function handleRate(recipeId: number, liked: boolean) {
    try {
      await apiFetch(`/recipes/${recipeId}/rating`, {
        method: "POST",
        body: JSON.stringify({ liked }),
      });
      setRatings((prev) => ({ ...prev, [recipeId]: liked }));
    } catch {
      // Rating is a soft signal - fail silently rather than interrupting the plan view.
    }
  }

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
        body: JSON.stringify({
          week_start_date: nextMonday(),
          dining_hall_meals: Number(diningHallMeals) || 0,
          weekly_cook_time_minutes: cookTimeMinutes ? Number(cookTimeMinutes) : null,
        }),
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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-heading text-2xl font-bold">Your meal plan</h1>
        <div className="flex items-center gap-3">
          <Link href="/pantry" className="text-sm underline">
            Pantry
          </Link>
          <Link href="/recipes" className="text-sm underline">
            Discover recipes
          </Link>
          <Link href="/dining" className="text-sm underline">
            Dining menus
          </Link>
        </div>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div className="flex flex-col gap-2">
          <Label htmlFor="dining-hall-meals">Dining hall meals this week</Label>
          <Input
            id="dining-hall-meals"
            type="number"
            min="0"
            max="21"
            className="w-28"
            value={diningHallMeals}
            onChange={(event) => setDiningHallMeals(event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-2">
          <Label htmlFor="cook-time-minutes">Cook time budget (min, optional)</Label>
          <Input
            id="cook-time-minutes"
            type="number"
            min="0"
            className="w-36"
            placeholder="No limit"
            value={cookTimeMinutes}
            onChange={(event) => setCookTimeMinutes(event.target.value)}
          />
        </div>
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
                          {entry?.is_dining_hall
                            ? "Dining hall"
                            : entry
                              ? `${entry.recipe_name} - $${entry.cost.toFixed(2)}`
                              : "-"}
                        </div>
                        {entry && !entry.is_dining_hall && entry.recipe_id !== null && (
                          <div className="mt-1 flex gap-1">
                            <Button
                              type="button"
                              size="xs"
                              variant={ratings[entry.recipe_id] === true ? "default" : "outline"}
                              onClick={() => handleRate(entry.recipe_id!, true)}
                            >
                              Like
                            </Button>
                            <Button
                              type="button"
                              size="xs"
                              variant={ratings[entry.recipe_id] === false ? "default" : "outline"}
                              onClick={() => handleRate(entry.recipe_id!, false)}
                            >
                              Skip
                            </Button>
                          </div>
                        )}
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
