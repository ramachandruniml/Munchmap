"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { apiFetch } from "@/lib/api";
import type { GroceryList } from "@/lib/types";

export default function GroceryListPage() {
  const params = useParams<{ id: string }>();
  const mealPlanId = params.id;

  const [groceryList, setGroceryList] = useState<GroceryList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<GroceryList>(`/meal-plans/${mealPlanId}/grocery-list`, { method: "POST" })
      .then(setGroceryList)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load grocery list"))
      .finally(() => setLoading(false));
  }, [mealPlanId]);

  async function toggleItem(itemId: number, checked: boolean) {
    if (!groceryList) return;
    setGroceryList({
      ...groceryList,
      items: groceryList.items.map((item) =>
        item.id === itemId ? { ...item, checked_off: checked } : item,
      ),
    });
    try {
      await apiFetch(`/grocery-lists/${groceryList.id}/items/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify({ checked_off: checked }),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <h1 className="text-2xl font-semibold">Grocery list</h1>

      {loading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {groceryList && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Items</CardTitle>
            <Badge variant="secondary">${groceryList.total_cost.toFixed(2)} total</Badge>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {groceryList.items.map((item) => (
              <label key={item.id} className="flex items-center gap-3 text-sm">
                <Checkbox
                  checked={item.checked_off}
                  onCheckedChange={(checked) => toggleItem(item.id, checked === true)}
                />
                <span className={item.checked_off ? "flex-1 line-through text-muted-foreground" : "flex-1"}>
                  {item.ingredient_name} - {item.total_quantity} {item.unit}
                </span>
                <span className="text-muted-foreground">${item.estimated_cost.toFixed(2)}</span>
              </label>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
