"use client";

import { motion } from "framer-motion";
import { Sparkles, TrendingUp } from "lucide-react";

import { HeroSearch } from "@/components/home/hero-search";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="bg-hero-glow pointer-events-none absolute inset-0" />
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-60 [mask-image:linear-gradient(to_bottom,black,transparent)]" />

      <div className="relative mx-auto max-w-7xl px-4 pt-20 pb-24 text-center sm:px-6 sm:pt-28 sm:pb-32">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-pill mx-auto mb-6 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm text-accent"
        >
          <Sparkles className="h-4 w-4" />
          Aggregated from LinkedIn · Indeed · Naukri · Internshala · Wellfound
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-balance mx-auto max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl"
        >
          One Search.{" "}
          <span className="text-brand-gradient">Every Opportunity.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-6 max-w-2xl text-base text-muted-foreground sm:text-lg"
        >
          Search thousands of jobs from the world&apos;s leading job portals in
          one place. Save favorites, set alerts, and apply directly on the
          original website.
        </motion.p>

        <div className="mt-10">
          <HeroSearch />
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="mt-10 inline-flex items-center gap-2 text-sm text-muted-foreground"
        >
          <TrendingUp className="h-4 w-4 text-success" />
          10,000+ jobs indexed every day across 6+ sources
        </motion.div>
      </div>
    </section>
  );
}