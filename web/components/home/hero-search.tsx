"use client";

import { motion } from "framer-motion";
import { MapPin, Search, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { POPULAR_SEARCHES } from "@/lib/types";

export function HeroSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");

  const submit = (q = query) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (location) params.set("location", location);
    router.push(`/jobs?${params.toString()}`);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="glass-strong mx-auto max-w-3xl rounded-2xl p-3 shadow-glow-lg"
    >
      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Job title, skills, or company…"
            className="h-12 border-0 bg-transparent pl-11 focus:ring-0 focus:border-0"
            aria-label="Search jobs"
          />
        </div>
        <div className="relative sm:w-56">
          <MapPin className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Location or Remote"
            className="h-12 border-0 bg-transparent pl-11 focus:ring-0 focus:border-0"
            aria-label="Job location"
          />
        </div>
        <Button size="lg" onClick={() => submit()} className="h-12">
          <Sparkles className="h-4 w-4" />
          Search
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2 px-2 pb-2 pt-3">
        <span className="text-xs text-muted-foreground">Popular:</span>
        {POPULAR_SEARCHES.slice(0, 5).map((term) => (
          <button
            key={term}
            onClick={() => submit(term)}
            className="glass-pill rounded-full px-3 py-1 text-xs text-muted-foreground transition-colors hover:text-white hover:border-primary/40"
          >
            {term}
          </button>
        ))}
      </div>
    </motion.div>
  );
}