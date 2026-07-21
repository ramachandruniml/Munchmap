"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import type { ExpiringRecipe, PantryItem } from "@/lib/types";

function isExpiringSoon(expiresAt: string | null): boolean {
  if (!expiresAt) return false;
  const daysUntil = (new Date(expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return daysUntil <= 5;
}

export default function PantryPage() {
  const [items, setItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expiringRecipes, setExpiringRecipes] = useState<ExpiringRecipe[]>([]);

  const [ingredientName, setIngredientName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("each");
  const [expiresAt, setExpiresAt] = useState("");
  const [saving, setSaving] = useState(false);

  function loadItems() {
    return apiFetch<PantryItem[]>("/pantry")
      .then((data) => {
        setItems(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load pantry"));
  }

  function loadExpiringRecipes() {
    return apiFetch<ExpiringRecipe[]>("/pantry/expiring-soon-recipes")
      .then(setExpiringRecipes)
      .catch(() => {
        // Non-critical - the pantry list itself already loaded successfully.
      });
  }

  useEffect(() => {
    Promise.all([loadItems(), loadExpiringRecipes()]).finally(() => setLoading(false));
  }, []);

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await apiFetch("/pantry", {
        method: "POST",
        body: JSON.stringify({
          ingredient_name: ingredientName,
          quantity: Number(quantity),
          unit,
          expires_at: expiresAt || null,
        }),
      });
      setIngredientName("");
      setQuantity("1");
      setExpiresAt("");
      await Promise.all([loadItems(), loadExpiringRecipes()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add item");
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateQuantity(item: PantryItem, nextQuantity: number) {
    if (nextQuantity < 0) return;
    try {
      await apiFetch(`/pantry/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity: nextQuantity, expires_at: item.expires_at }),
      });
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    }
  }

  async function handleUpdateExpiration(item: PantryItem, nextExpiresAt: string) {
    try {
      await apiFetch(`/pantry/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity: item.quantity, expires_at: nextExpiresAt || null }),
      });
      await Promise.all([loadItems(), loadExpiringRecipes()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update item");
    }
  }

  async function handleDelete(item: PantryItem) {
    try {
      await apiFetch(`/pantry/${item.id}`, { method: "DELETE" });
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove item");
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <h1 className="font-heading text-2xl font-bold">Pantry</h1>
      <p className="text-sm text-muted-foreground">
        Items you already have get subtracted from future grocery lists.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add an item</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="ingredient-name">Ingredient</Label>
              <Input
                id="ingredient-name"
                required
                placeholder="rice"
                value={ingredientName}
                onChange={(event) => setIngredientName(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="quantity">Quantity</Label>
              <Input
                id="quantity"
                type="number"
                min="0"
                step="0.01"
                required
                className="w-24"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="unit">Unit</Label>
              <Input
                id="unit"
                required
                placeholder="cup, gram, each"
                className="w-32"
                value={unit}
                onChange={(event) => setUnit(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="expires-at">Expires (optional)</Label>
              <Input
                id="expires-at"
                type="date"
                className="w-40"
                value={expiresAt}
                onChange={(event) => setExpiresAt(event.target.value)}
              />
            </div>
            <Button type="submit" disabled={saving}>
              {saving ? "Adding..." : "Add"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {expiringRecipes.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Use it up soon</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            <p className="text-sm text-muted-foreground">
              Recipes that use pantry ingredients expiring within 5 days.
            </p>
            {expiringRecipes.map((recipe) => (
              <div key={recipe.recipe_id} className="flex flex-col gap-1 rounded-md border p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{recipe.recipe_name}</span>
                  <span className="text-sm text-muted-foreground">
                    ${recipe.cost_per_serving.toFixed(2)}/serving
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {recipe.expiring_ingredients.map((name) => (
                    <Badge key={name} variant="secondary">
                      {name}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}
      {loading && <p className="text-sm text-muted-foreground">Loading...</p>}

      {!loading && items.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Nothing in your pantry yet - add what you already have on hand.
        </p>
      )}

      {items.length > 0 && (
        <div className="flex flex-col gap-2">
          {items.map((item) => (
            <div
              key={item.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-md border p-3"
            >
              <div className="flex items-center gap-2">
                <span className="font-medium capitalize">{item.ingredient_name}</span>
                {isExpiringSoon(item.expires_at) && (
                  <Badge variant="destructive">Expires soon</Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => handleUpdateQuantity(item, item.quantity - 1)}
                >
                  -
                </Button>
                <span className="w-24 text-center text-sm text-muted-foreground">
                  {item.quantity} {item.unit}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => handleUpdateQuantity(item, item.quantity + 1)}
                >
                  +
                </Button>
                <Input
                  type="date"
                  className="w-40"
                  value={item.expires_at ?? ""}
                  onChange={(event) => handleUpdateExpiration(item, event.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => handleDelete(item)}
                >
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
