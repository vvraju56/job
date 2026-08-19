"use client";

import { motion } from "framer-motion";
import { Briefcase, Building2, Search, Users } from "lucide-react";
import { formatNumber } from "@/lib/utils";

const STATS = [
  { icon: Briefcase, value: 12500, suffix: "+", label: "Live Jobs" },
  { icon: Building2, value: 4200, suffix: "+", label: "Companies" },
  { icon: Users, value: 185000, suffix: "+", label: "Job Seekers" },
  { icon: Search, value: 6, suffix: "", label: "Job Sources" },
];

export function StatsSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div className="glass rounded-3xl p-8">
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.1 }}
              className="flex flex-col items-center gap-3 text-center"
            >
              <span className="glass-pill flex h-12 w-12 items-center justify-center rounded-2xl text-primary">
                <stat.icon className="h-6 w-6" />
              </span>
              <div>
                <p className="text-2xl font-extrabold sm:text-3xl">
                  {formatNumber(stat.value)}
                  <span className="text-accent">{stat.suffix}</span>
                </p>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}