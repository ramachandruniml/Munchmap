export interface Profile {
  id: string;
  weekly_budget: number;
  equipment: string[];
  dietary_restrictions: string[];
  allergies: string[];
  dislikes: string[];
  calorie_target: number | null;
  protein_target_g: number | null;
  carb_target_g: number | null;
  fat_target_g: number | null;
}

export interface MealPlanEntry {
  id: number;
  day_of_week: number;
  meal_slot: "breakfast" | "lunch" | "dinner";
  recipe_id: number | null;
  recipe_name: string | null;
  cost: number;
  is_dining_hall: boolean;
}

export interface MealPlan {
  id: number;
  week_start_date: string;
  total_cost: number;
  status: string;
  dining_hall_meals: number;
  weekly_cook_time_minutes: number | null;
  entries: MealPlanEntry[];
}

export interface GroceryListItem {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  total_quantity: number;
  unit: string;
  estimated_cost: number;
  checked_off: boolean;
}

export interface GroceryList {
  id: number;
  meal_plan_id: number;
  items: GroceryListItem[];
  total_cost: number;
}

export interface PantryItem {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  quantity: number;
  unit: string;
  expires_at: string | null;
}

export interface ExpiringRecipe {
  recipe_id: number;
  recipe_name: string;
  cost_per_serving: number;
  expiring_ingredients: string[];
  soonest_expiration: string;
}

export interface RecipeSearchResult {
  id: number;
  name: string;
  cost_per_serving: number;
  calories: number;
  protein_g: number;
  carb_g: number;
  fat_g: number;
  diet_tags: string[];
}

export interface MenuItem {
  id: number;
  name: string;
  station: string;
  diet_tags: string[];
}

export interface Menu {
  id: number;
  dining_hall_name: string;
  menu_date: string;
  items: MenuItem[];
}

export interface Substitute {
  id: number;
  name: string;
  similarity: number;
}

export interface IngredientSubstitutes {
  ingredient_id: number;
  ingredient_name: string;
  substitutes: Substitute[];
}

export const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
export const MEAL_SLOTS = ["breakfast", "lunch", "dinner"] as const;
