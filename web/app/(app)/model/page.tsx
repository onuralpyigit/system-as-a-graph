import { PageHeader } from "@/components/app-shell/page-header";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ModelPage() {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Model" />
      <div className="px-6">
        <Tabs defaultValue="browse">
          <TabsList>
            <TabsTrigger value="browse">Browse</TabsTrigger>
            <TabsTrigger value="edit">Edit</TabsTrigger>
          </TabsList>
          <TabsContent value="browse" className="text-sm text-muted-foreground">
            Browse screen not yet built.
          </TabsContent>
          <TabsContent value="edit" className="text-sm text-muted-foreground">
            Edit screen not yet built.
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
