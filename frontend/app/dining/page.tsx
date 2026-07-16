"use client";

import { useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import type { Menu } from "@/lib/types";

const textareaClassName =
  "min-h-32 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-base transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm dark:bg-input/30";

function todayDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export default function DiningPage() {
  const [hallName, setHallName] = useState("");
  const [menuDate, setMenuDate] = useState(todayDate());
  const [rawText, setRawText] = useState("");
  const [pasting, setPasting] = useState(false);
  const [pasteError, setPasteError] = useState<string | null>(null);

  const [lookupHallName, setLookupHallName] = useState("");
  const [lookupDate, setLookupDate] = useState(todayDate());
  const [menu, setMenu] = useState<Menu | null>(null);
  const [loadingMenu, setLoadingMenu] = useState(false);
  const [lookupError, setLookupError] = useState<string | null>(null);

  async function handlePaste(event: FormEvent) {
    event.preventDefault();
    setPasting(true);
    setPasteError(null);
    try {
      const result = await apiFetch<Menu>("/dining/menus/paste", {
        method: "POST",
        body: JSON.stringify({
          dining_hall_name: hallName,
          menu_date: menuDate,
          raw_text: rawText,
        }),
      });
      setMenu(result);
      setLookupHallName(hallName);
      setLookupDate(menuDate);
      setRawText("");
    } catch (err) {
      setPasteError(err instanceof Error ? err.message : "Failed to parse menu");
    } finally {
      setPasting(false);
    }
  }

  async function handleLookup(event: FormEvent) {
    event.preventDefault();
    setLoadingMenu(true);
    setLookupError(null);
    try {
      const result = await apiFetch<Menu>(
        `/dining/menus?dining_hall_name=${encodeURIComponent(lookupHallName)}&menu_date=${lookupDate}`,
      );
      setMenu(result);
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : "Menu not found");
      setMenu(null);
    } finally {
      setLoadingMenu(false);
    }
  }

  const itemsByStation = menu?.items.reduce<Record<string, typeof menu.items>>((acc, item) => {
    (acc[item.station] ??= []).push(item);
    return acc;
  }, {});

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-6">
      <h1 className="font-heading text-2xl font-bold">Dining hall menus</h1>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Paste a menu</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handlePaste} className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-3">
              <div className="flex flex-col gap-2">
                <Label htmlFor="hall-name">Dining hall</Label>
                <Input
                  id="hall-name"
                  required
                  placeholder="North Hall"
                  value={hallName}
                  onChange={(event) => setHallName(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="menu-date">Date</Label>
                <Input
                  id="menu-date"
                  type="date"
                  required
                  value={menuDate}
                  onChange={(event) => setMenuDate(event.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="raw-text">Raw menu text</Label>
              <textarea
                id="raw-text"
                required
                className={textareaClassName}
                placeholder="Paste the dining hall's menu text or HTML here"
                value={rawText}
                onChange={(event) => setRawText(event.target.value)}
              />
            </div>
            {pasteError && <p className="text-sm text-destructive">{pasteError}</p>}
            <Button type="submit" disabled={pasting} className="self-start">
              {pasting ? "Parsing..." : "Parse and save"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Look up a menu</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLookup} className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-2">
              <Label htmlFor="lookup-hall">Dining hall</Label>
              <Input
                id="lookup-hall"
                required
                value={lookupHallName}
                onChange={(event) => setLookupHallName(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="lookup-date">Date</Label>
              <Input
                id="lookup-date"
                type="date"
                required
                value={lookupDate}
                onChange={(event) => setLookupDate(event.target.value)}
              />
            </div>
            <Button type="submit" variant="outline" disabled={loadingMenu}>
              {loadingMenu ? "Loading..." : "View menu"}
            </Button>
          </form>
          {lookupError && <p className="mt-2 text-sm text-destructive">{lookupError}</p>}
        </CardContent>
      </Card>

      {menu && itemsByStation && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {menu.dining_hall_name} - {menu.menu_date}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {Object.entries(itemsByStation).map(([station, items]) => (
              <div key={station} className="flex flex-col gap-2">
                <h3 className="text-sm font-medium">{station}</h3>
                <div className="flex flex-col gap-1">
                  {items.map((item) => (
                    <div key={item.id} className="flex items-center gap-2 text-sm">
                      <span>{item.name}</span>
                      {item.diet_tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
