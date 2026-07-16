"use client";

import { useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api";
import type { RecipeSearchResult } from "@/lib/types";

export default function RecipesPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<RecipeSearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<RecipeSearchResult[]>(
        `/recipes/search?q=${encodeURIComponent(query)}`,
      );
      setResults(data);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-6">
      <h1 className="font-heading text-2xl font-bold">Discover recipes</h1>
      <p className="text-sm text-muted-foreground">
        Describe what you&apos;re craving and find matching recipes from the catalog.
      </p>

      <form onSubmit={handleSearch} className="flex gap-3">
        <Input
          placeholder="spicy chicken bowl"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </Button>
      </form>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {searched && !loading && results.length === 0 && (
        <p className="text-sm text-muted-foreground">No matching recipes found.</p>
      )}

      {results.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {results.map((recipe) => (
            <Card key={recipe.id}>
              <CardHeader>
                <CardTitle className="text-base">{recipe.name}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                  <Badge variant="secondary">${recipe.cost_per_serving.toFixed(2)}/serving</Badge>
                  <Badge variant="secondary">{recipe.calories} cal</Badge>
                  {recipe.diet_tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <div className="text-xs text-muted-foreground">
                  {recipe.protein_g}g protein · {recipe.carb_g}g carbs · {recipe.fat_g}g fat
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
