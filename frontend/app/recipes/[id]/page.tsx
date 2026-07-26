"use client";

import { Heart } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { RecipeDetail } from "@/lib/types";

export default function RecipeDetailPage() {
  const params = useParams<{ id: string }>();
  const recipeId = params.id;

  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [favoriting, setFavoriting] = useState(false);

  useEffect(() => {
    apiFetch<RecipeDetail>(`/recipes/${recipeId}`)
      .then(setRecipe)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load recipe"))
      .finally(() => setLoading(false));
  }, [recipeId]);

  async function handleFavorite() {
    if (!recipe) return;
    const nextLiked = recipe.liked !== true;
    setFavoriting(true);
    try {
      await apiFetch(`/recipes/${recipeId}/rating`, {
        method: "POST",
        body: JSON.stringify({ liked: nextLiked }),
      });
      setRecipe({ ...recipe, liked: nextLiked });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update favorite");
    } finally {
      setFavoriting(false);
    }
  }

  if (loading) {
    return <p className="p-6 text-sm text-muted-foreground">Loading...</p>;
  }
  if (error || !recipe) {
    return <p className="p-6 text-sm text-destructive">{error ?? "Recipe not found"}</p>;
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3">
          <CardTitle className="font-heading text-2xl">{recipe.name}</CardTitle>
          <Button
            type="button"
            variant={recipe.liked === true ? "default" : "outline"}
            size="icon"
            disabled={favoriting}
            onClick={handleFavorite}
            aria-label="Favorite this recipe"
          >
            <Heart className={recipe.liked === true ? "fill-current" : ""} />
          </Button>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">${recipe.cost_per_serving.toFixed(2)}/serving</Badge>
            <Badge variant="secondary">{recipe.cook_time_minutes} min</Badge>
            <Badge variant="secondary">{recipe.servings} servings</Badge>
            <Badge variant="secondary">{recipe.calories} cal</Badge>
            {recipe.diet_tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>

          <div className="text-sm text-muted-foreground">
            {recipe.protein_g}g protein &middot; {recipe.carb_g}g carbs &middot; {recipe.fat_g}g fat
          </div>

          {recipe.equipment_required.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {recipe.equipment_required.map((eq) => (
                <Badge key={eq} variant="outline">
                  {eq.replace("_", " ")}
                </Badge>
              ))}
            </div>
          )}

          <div>
            <h3 className="font-heading mb-2 text-base font-bold">Ingredients</h3>
            <ul className="flex flex-col gap-1 text-sm text-muted-foreground">
              {recipe.ingredients.map((ing) => (
                <li key={ing.ingredient_id}>
                  {ing.quantity} {ing.unit} {ing.name}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-heading mb-2 text-base font-bold">Instructions</h3>
            <p className="whitespace-pre-line text-sm text-muted-foreground">
              {recipe.instructions}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
