import { Card } from "@/components/ui/card";

interface TimelineItem {
  year: string;
  title: string;
  company: string;
  description: string;
}

const timelineData: TimelineItem[] = [
  {
    year: "2025",
    title: "Chief Architect",
    company: "Constellations AI",
    description: "Leading the design and implementation of mission-critical AI systems across finance, defense, and personal augmentation—creating orchestration frameworks that fuse multi-agent coordination, contextual memory, and real-time reasoning to enable intelligent, adaptive behavior at scale."
  },
  {
    year: "2025",
    title: "STEM Tutor, Research",
    company: "xAI",
    description: "Contributed to the development of advanced reasoning capabilities in Grok by designing STEM evaluation tasks that stress-test conceptual depth, chain-of-thought reasoning, and symbolic logic—advancing LLM alignment and trustworthiness in complex, real-world domains."
  },
  {
    year: "2023-2024",
    title: "CTO",
    company: "Special Operations Command, Pacific (SOCPAC)",
    description: "Led the development of the Indo-Pacific tech strategy, aligning autonomous systems, AI infrastructure, and joint operational priorities to modernize U.S. Special Operations capabilities—bridging defense innovation, interagency coordination, and forward-operating resilience in support of national security objectives."
  },
  {
    year: "2021-2023",
    title: "Lead Integration Engineer",
    company: "Joint Special Operations Command (JSOC)",
    description: "Architected next-generation decision support systems and AI-integrated infrastructure—deploying a secure, Kubernetes-native Battlelab that enabled rapid prototyping, accelerated tech adoption cycles, and transformed mission planning through scalable, modular innovation in high-stakes operational environments."
  },
  {
    year: "2016-2021",
    title: "CEO and Founder",
    company: "Elysian Labs",
    description: "Founded and scaled a mission-driven defense technology firm supporting SOCOM, DARPA, and SCO with cutting-edge AI/ML systems, human-machine interfaces, and advanced sensor platforms. Led all facets of growth from securing $3M+ in non-dilutive federal funding to expanding R&D operations and delivering field-ready solutions that shaped next-generation national security capabilities."
  },
  {
    year: "2008-2016",
    title: "Senior Member of Technical Staff",
    company: "Sandia National Laboratories",
    description: "Directed a 50-person cross-laboratory team with a $13M budget to deliver strategic roadmaps for nuclear stockpile safety—securing continued congressional funding and influencing national defense priorities. Led systems-level innovation in high-assurance environments, bridging technical rigor with long-term strategic planning in one of the most mission-critical domains in U.S. security."
  }
];

export const Timeline = () => {
  return (
    <div className="relative max-w-4xl mx-auto">
      {/* Central timeline line */}
      <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gradient-to-b from-stellar via-primary to-stellar/20 transform -translate-x-1/2"></div>
      
      <div className="space-y-12">
        {timelineData.map((item, index) => {
          const isLeft = index % 2 === 0;
          return (
            <div key={index} className="relative flex items-center">
              {/* Timeline dot */}
              <div className="absolute z-10 w-8 h-8 bg-stellar rounded-full flex items-center justify-center animate-stellar-pulse"
                   style={{ 
                     left: '50%',
                     top: '50%',
                     transform: `translate(${isLeft ? '-34px' : '1px'}, -50%)`
                   }}>
                <div className="w-3 h-3 bg-stellar-glow rounded-full"></div>
              </div>
              
              {/* Content - alternating left and right */}
              <div className={`w-5/12 ${isLeft ? 'pr-8 text-right' : 'ml-auto pl-8 text-left'}`}>
                <Card className="p-6 bg-card/80 backdrop-blur-sm border-stellar/20 hover:border-stellar/40 transition-all duration-500 hover:shadow-[0_0_30px_hsl(var(--stellar)_/_0.2)]">
                  <div className="mb-3">
                    <div className={`${isLeft ? 'text-right' : 'text-left'}`}>
                      <h3 className="text-xl font-bold text-foreground mb-1">{item.title}</h3>
                      <p className="text-stellar font-medium mb-2">{item.company}</p>
                      <span className="inline-block text-sm bg-stellar/20 text-stellar-glow px-3 py-1 rounded-full">
                        {item.year}
                      </span>
                    </div>
                  </div>
                  <p className={`text-muted-foreground leading-relaxed ${isLeft ? 'text-right' : 'text-left'}`}>
                    {item.description}
                  </p>
                </Card>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};