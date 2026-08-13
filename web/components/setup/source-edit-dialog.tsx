"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SelectNative } from "@/components/ui/select-native";
import type { DataSourceConfigureRequest, DataSourceResponse } from "@/lib/api-types";

import { SOURCE_TYPES } from "./source-types";

// Each source type is served by exactly one adapter (msd/src/adapters/factory.py),
// so the access method is a fact of the type, not an independent choice.
const ACCESS_METHOD_BY_SOURCE_TYPE: Record<string, string> = {
  configuration_management_database: "sql",
  source_repository: "git_https",
  package_repository: "rest",
  network_topology: "ansible",
};

const ACCESS_METHOD_LABELS: Record<string, string> = {
  git_https: "Git over HTTPS",
  sql: "SQL",
  rest: "REST",
  ansible: "Ansible",
};

interface SourceEditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  source: DataSourceResponse | null;
  /** Source type to preselect when adding a new source (ignored when editing). */
  defaultSourceType?: string;
  onSubmit: (payload: DataSourceConfigureRequest) => void;
  isSubmitting: boolean;
}

interface FormValues {
  source_type: string;
  name: string;
  connection_address: string;
  username: string;
  secret: string;
  priority: number;
}

export function SourceEditDialog({
  open,
  onOpenChange,
  source,
  defaultSourceType,
  onSubmit,
  isSubmitting,
}: SourceEditDialogProps) {
  const isEditing = source !== null;
  const { register, handleSubmit, reset, watch } = useForm<FormValues>();
  const sourceType = watch("source_type");
  const accessMethod = ACCESS_METHOD_BY_SOURCE_TYPE[sourceType];

  useEffect(() => {
    if (!open) return;
    reset({
      source_type: source?.source_type ?? defaultSourceType ?? SOURCE_TYPES[0].value,
      name: source?.name ?? "",
      connection_address: source?.connection_address ?? "",
      username: source?.username ?? "",
      secret: "",
      priority: source?.priority ?? 0,
    });
  }, [open, source, defaultSourceType, reset]);

  function submit(values: FormValues) {
    onSubmit({
      source_type: values.source_type,
      name: values.name,
      access_method: ACCESS_METHOD_BY_SOURCE_TYPE[values.source_type],
      connection_address: values.connection_address,
      username: values.username,
      secret: values.secret ? values.secret : null,
      priority: Number(values.priority),
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? `Edit ${source.name}` : "Add data source"}</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-3" onSubmit={handleSubmit(submit)}>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="source_type">Source type</Label>
              <SelectNative id="source_type" disabled={isEditing} {...register("source_type")}>
                {SOURCE_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </SelectNative>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="access_method">Access method</Label>
              <Input
                id="access_method"
                value={ACCESS_METHOD_LABELS[accessMethod] ?? ""}
                disabled
                readOnly
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input id="name" disabled={isEditing} {...register("name", { required: true })} />
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="connection_address">Connection address</Label>
            <Input
              id="connection_address"
              placeholder="Base URL, DSN, or path"
              {...register("connection_address", { required: true })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Username</Label>
              <Input id="username" {...register("username")} />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="priority">Priority</Label>
              <Input id="priority" type="number" {...register("priority")} />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="secret">Secret</Label>
            <Input
              id="secret"
              type="password"
              autoComplete="new-password"
              placeholder={
                isEditing && source?.secret_set ? "Stored — leave blank to keep it" : "Secret"
              }
              {...register("secret")}
            />
          </div>

          <DialogFooter>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
