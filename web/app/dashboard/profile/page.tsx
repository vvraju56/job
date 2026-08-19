"use client";

import { Check, Loader2, LogOut, Save } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { GlassCard } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import { usersService } from "@/lib/services";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();
  const router = useRouter();

  const [name, setName] = useState(user?.name ?? "");
  const [headline, setHeadline] = useState(user?.headline ?? "");
  const [bio, setBio] = useState(user?.bio ?? "");
  const [location, setLocation] = useState(user?.location ?? "");
  const [experience, setExperience] = useState(user?.experience ?? 0);
  const [skillsInput, setSkillsInput] = useState((user?.skills ?? []).join(", "));
  const [remoteOnly, setRemoteOnly] = useState(
    Boolean(user?.preferences?.remote_only),
  );
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await usersService.updateProfile({
        name,
        headline: headline || null,
        bio: bio || null,
        location: location || null,
        experience: Number(experience) || 0,
        skills: skillsInput
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      await usersService.updatePreferences({
        remote_only: remoteOnly,
        job_types: [],
        locations: location ? [location] : [],
        keywords: skillsInput
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Profile & Preferences</h2>
          <p className="text-sm text-muted-foreground">
            Keep your profile updated for better job recommendations.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          <LogOut className="h-4 w-4" /> Sign out
        </Button>
      </div>

      <form onSubmit={save} className="space-y-6">
        <GlassCard className="p-6 sm:p-8">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-semibold">Full name</label>
              <Input value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold">Email</label>
              <Input value={user?.email ?? ""} disabled />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm font-semibold">Headline</label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
                placeholder="e.g. Senior Flutter Developer"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold">Location</label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Chennai, India"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-semibold">
                Experience (years)
              </label>
              <Input
                type="number"
                min={0}
                value={experience}
                onChange={(e) => setExperience(Number(e.target.value))}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm font-semibold">Bio</label>
              <Textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell recruiters a little about yourself…"
                className="min-h-[100px]"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="mb-1 block text-sm font-semibold">Skills</label>
              <Input
                value={skillsInput}
                onChange={(e) => setSkillsInput(e.target.value)}
                placeholder="e.g. Flutter, Dart, Firebase, Riverpod"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Comma-separated. Used for personalized job recommendations.
              </p>
            </div>
          </div>
        </GlassCard>

        <GlassCard className="p-6 sm:p-8">
          <h3 className="mb-4 font-semibold">Job preferences</h3>
          <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="h-4 w-4 accent-primary"
            />
            <span className="text-sm">Only recommend remote jobs</span>
          </label>
        </GlassCard>

        {error && (
          <p className="rounded-xl border border-warning/30 bg-warning/10 px-4 py-2.5 text-sm text-warning">
            {error}
          </p>
        )}

        <Button type="submit" disabled={saving} className={cn(saved && "bg-success")}>
          {saving ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : saved ? (
            <Check className="h-4 w-4" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {saving ? "Saving…" : saved ? "Saved!" : "Save changes"}
        </Button>
      </form>
    </div>
  );
}