"use client";

import React from "react";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ResearchCardProps {
  report: string;
  learnings: string[];
  visited_urls?: string[];
}

export default function ResearchCard({
  report,
  learnings,
  visited_urls = [],
}: ResearchCardProps) {
  return (
    <div className="border rounded-lg p-4 bg-white dark:bg-gray-800 shadow">
      <h3 className="font-bold text-lg text-primary mb-4">Research Results</h3>

      <Accordion type="multiple" className="w-full space-y-4">
        {/* Full Report Section */}
        <AccordionItem value="report">
          <AccordionTrigger className="text-base font-medium">
            Full Report
          </AccordionTrigger>
          <AccordionContent>
            <ScrollArea className="h-[400px] w-full rounded-md border p-4">
              <div className="whitespace-pre-wrap text-sm">{report}</div>
            </ScrollArea>
          </AccordionContent>
        </AccordionItem>

        {/* Key Learnings Section */}
        <AccordionItem value="learnings">
          <AccordionTrigger className="text-base font-medium">
            Key Learnings ({learnings.length})
          </AccordionTrigger>
          <AccordionContent>
            <ScrollArea className="h-[300px] w-full rounded-md border p-4">
              <ul className="list-disc list-inside space-y-2">
                {learnings.map((learning, index) => (
                  <li key={index} className="text-sm">
                    {learning}
                  </li>
                ))}
              </ul>
            </ScrollArea>
          </AccordionContent>
        </AccordionItem>

        {/* Sources Section */}
        {visited_urls && visited_urls.length > 0 && (
          <AccordionItem value="sources">
            <AccordionTrigger className="text-base font-medium">
              Sources ({visited_urls.length})
            </AccordionTrigger>
            <AccordionContent>
              <ScrollArea className="h-[200px] w-full rounded-md border p-4">
                <ul className="list-disc list-inside space-y-2">
                  {visited_urls.map((url, index) => (
                    <li key={index} className="text-sm break-all">
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 dark:text-blue-400 hover:underline"
                      >
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </AccordionContent>
          </AccordionItem>
        )}
      </Accordion>
    </div>
  );
}
