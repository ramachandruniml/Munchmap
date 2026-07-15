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
  day_of_week: number;
  meal_slot: "breakfast" | "lunch" | "dinner";
  recipe_id: number;
  recipe_name: string;
  cost: number;
}

export interface MealPlan {
  id: number;
  week_start_date: string;
  total_cost: number;
  status: string;
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

export const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
export const MEAL_SLOTS = ["breakfast", "lunch", "dinner"] as const;
