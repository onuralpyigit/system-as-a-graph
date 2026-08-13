import { PageHeader } from "@/components/app-shell/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function AnalyticalDataPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Analytical Data" />
      <div className="px-6">
        <Tabs defaultValue="field-records">
          <TabsList>
            <TabsTrigger value="field-records">Field Records</TabsTrigger>
            <TabsTrigger value="scenario-generator">Scenario Generator</TabsTrigger>
          </TabsList>
          <TabsContent value="field-records" className="text-sm text-muted-foreground">
            Field Records screen not yet built.
          </TabsContent>
          <TabsContent value="scenario-generator" className="text-sm text-muted-foreground">
            Scenario Generator screen not yet built.
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
