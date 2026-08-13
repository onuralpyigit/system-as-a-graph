import { PageHeader } from "@/components/app-shell/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function FindingsPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Findings" />
      <div className="px-6">
        <Tabs defaultValue="verification">
          <TabsList>
            <TabsTrigger value="verification">Verification</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="evaluation">Evaluation</TabsTrigger>
            <TabsTrigger value="reports">Reports</TabsTrigger>
          </TabsList>
          <TabsContent value="verification" className="text-sm text-muted-foreground">
            Verification screen not yet built.
          </TabsContent>
          <TabsContent value="analysis" className="text-sm text-muted-foreground">
            Analysis screen not yet built.
          </TabsContent>
          <TabsContent value="evaluation" className="text-sm text-muted-foreground">
            Evaluation screen not yet built.
          </TabsContent>
          <TabsContent value="reports" className="text-sm text-muted-foreground">
            Reports screen not yet built.
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
