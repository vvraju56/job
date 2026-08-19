"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Cloud,
  Code,
  Layout,
  Megaphone,
  Palette,
  Server,
  Smartphone,
} from "lucide-react";
import Link from "next/link";

import { CATEGORIES } from "@/lib/types";

const ICONS: Record<string, typeof Code> = {
  code: Code,
  server: Server,
  smartphone: Smartphone,
  brain: Brain,
  palette: Palette,
  cloud: Cloud,
  layout: Layout,
  megaphone: Megaphone,
};

export function CategoriesSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
      <div className="mb-8 text-center">
        <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-accent">
          Explore
        </p>
        <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Browse by Category
        </h2>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {CATEGORIES.map((cat, i) => {
          const Icon = ICONS[cat.icon] ?? Code;
          return (
            <motion.div
              key={cat.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.05 }}
            >
              <Link
                href={`/jobs?q=${encodeURIComponent(cat.query)}`}
                className="glass card-hover flex items-center gap-4 rounded-2xl p-5"
              >
                <span className="btn-brand-gradient flex h-11 w-11 shrink-0 items-center justify-center rounded-xl">
                  <Icon className="h-5 w-5" />
                </span>
                <span className="font-semibold">{cat.label}</span>
              </Link>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}