"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import type { Profile } from "@/lib/types";

const EQUIPMENT_OPTIONS = ["microwave", "mini_fridge", "hot_plate", "stovetop", "oven", "full_kitchen"];
const DIET_OPTIONS = ["vegetarian", "vegan", "gluten-free", "dairy-free", "low-carb"];

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
}

export default function OnboardingPage() {
  const router = useRouter();
  const [weeklyBudget, setWeeklyBudget] = useState("50");
  const [equipment, setEquipment] = useState<string[]>([]);
  const [dietaryRestrictions, setDietaryRestrictions] = useState<string[]>([]);
  const [allergies, setAllergies] = useState("");
  const [dislikes, setDislikes] = useState("");
  const [calorieTarget, setCalorieTarget] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    apiFetch<Profile>("/profile")
      .then((profile) => {
        setWeeklyBudget(String(profile.weekly_budget));
        setEquipment(profile.equipment);
        setDietaryRestrictions(profile.dietary_restrictions);
        setAllergies(profile.allergies.join(", "));
        setDislikes(profile.dislikes.join(", "));
        setCalorieTarget(profile.calorie_target ? String(profile.calorie_target) : "");
      })
      .catch(() => {
        // No profile yet - fine, this is a first-time onboarding.
      });
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiFetch("/profile", {
        method: "PUT",
        body: JSON.stringify({
          weekly_budget: Number(weeklyBudget),
          equipment,
          dietary_restrictions: dietaryRestrictions,
          allergies: allergies
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          dislikes: dislikes
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
          calorie_target: calorieTarget ? Number(calorieTarget) : null,
        }),
      });
      router.push("/plan");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center p-6">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Set up your profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-2">
              <Label htmlFor="budget">Weekly grocery budget ($)</Label>
              <Input
                id="budget"
                type="number"
                min="0"
                step="0.01"
                required
                value={weeklyBudget}
                onChange={(event) => setWeeklyBudget(event.target.value)}
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label>Equipment available</Label>
              <div className="grid grid-cols-2 gap-2">
                {EQUIPMENT_OPTIONS.map((option) => (
                  <label key={option} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={equipment.includes(option)}
                      onCheckedChange={() => setEquipment((prev) => toggle(prev, option))}
                    />
                    {option.replace("_", " ")}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Label>Dietary restrictions</Label>
              <div className="grid grid-cols-2 gap-2">
                {DIET_OPTIONS.map((option) => (
                  <label key={option} className="flex items-center gap-2 text-sm">
                    <Checkbox
                      checked={dietaryRestrictions.includes(option)}
                      onCheckedChange={() =>
                        setDietaryRestrictions((prev) => toggle(prev, option))
                      }
                    />
                    {option}
                  </label>
                ))}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="allergies">Allergies (comma-separated)</Label>
              <Input
                id="allergies"
                placeholder="peanut, shellfish"
                value={allergies}
                onChange={(event) => setAllergies(event.target.value)}
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="dislikes">Dislikes (comma-separated)</Label>
              <Input
                id="dislikes"
                placeholder="cilantro, mushroom"
                value={dislikes}
                onChange={(event) => setDislikes(event.target.value)}
              />
            </div>

            <div className="flex flex-col gap-2">
              <Label htmlFor="calories">Daily calorie target (optional)</Label>
              <Input
                id="calories"
                type="number"
                min="0"
                value={calorieTarget}
                onChange={(event) => setCalorieTarget(event.target.value)}
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Save profile"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
