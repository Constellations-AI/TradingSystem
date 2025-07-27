import { Timeline } from "@/components/Timeline";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import constellationHero from "@/assets/constellation-hero.jpg";
import headshot from "@/assets/Headshot.jpg";

const LandingPage = () => {
  const projects = [
    {
      title: "Multiagent Trading System",
      description: [
        "This advanced trading platform features multiple AI agents designed for both long-term investing and intraday momentum trading, each configured with a distinct trading personality profile. These profiles encode strategy preferences - such as value investing, innovation-focused growth, or aggressive day trading - and guide agent behavior in real time.",
        "The system combines technical indicators (RSI, SMA, volume analysis) with LLM-based reasoning to interpret earnings reports, news sentiment, and macroeconomic trends. Powered by LangChain research agents and connected to live data streams via Polygon and Alpha Vantage APIs, each trader operates within a disciplined risk management framework enforced by evaluators.",
        "This hybrid architecture delivers decision-making that is both data-driven and context-aware, enabling intelligent trading aligned with distinct, human-inspired strategies."
      ],
      status: "active",
      link: "/dashboard"
    },
    {
      title: "Fine-tune Personal Assistant",
      description: [
        "This is a digital twin operating at sub-second response times - engineered for secure environments.",
        "Built on a fine-tuned LLM that mirrors the user's communication style, preferences, and decision logic, this AI assistant leverages federated learning to enable continuous model refinement and personalization across air-gapped, compartmentalized, or enterprise-secure deployments without centralizing sensitive data. A vector database supports rapid, semantically rich memory recall, while a graph database preserves persistent relationships, timelines, and mission-critical context.",
        "Routine and low-risk decisions - such as task execution, research, and scheduling - are handled autonomously. Higher-impact actions are escalated for user confirmation. This dual-memory architecture, grounded in both process and intuition, ensures the assistant evolves in lockstep with the user's thought patterns - enabling trusted delegation in environments where precision, privacy, and speed are mission-essential."
      ],
      status: "coming-soon"
    },
    {
      title: "Course of Action Generation",
      description: [
        "Our simulation framework leverages Unity for real-time 3D visualization and multi-agent coordination, creating a flexible testbed for prototyping autonomous behaviors across air, land, sea, and cyber domains. Hybrid A* path planning enables smooth, deterministic trajectory generation through complex and constrained environments.",
        "To support real-time adaptation and long-term optimization, we integrate reinforcement learning using PPO for high-level decision-making and SAC for continuous control tasks. Separate training and inference pipelines ensure low-latency performance, enabling centralized training with decentralized execution for coordinated multi-agent behavior.",
        "The result is a hybrid autonomy architecture that blends rule-based planning with adaptive learning, enabling agents to generate and evaluate mission-relevant Courses of Action (COAs) under dynamic and uncertain conditions."
      ],
      status: "coming-soon"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
        {/* Background */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${constellationHero})` }}
        >
          <div className="absolute inset-0 bg-gradient-to-b from-background/20 via-background/60 to-background"></div>
        </div>
        
        {/* Content */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <div className="animate-float">
            <h1 className="text-6xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-stellar via-primary-glow to-nebula bg-clip-text text-transparent">
              Constellations AI
            </h1>
            <div className="h-1 w-32 bg-gradient-to-r from-stellar to-nebula mx-auto mb-8 animate-glow"></div>
          </div>
          
          <div className="max-w-6xl mx-auto space-y-6">
            <p className="text-xl md:text-2xl text-foreground/90 leading-relaxed">
              Intelligence, orchestrated.
            </p>
            
            <p className="text-lg text-muted-foreground leading-relaxed">
              We specialize in orchestrating autonomous agents that operate with memory, context, and purpose. At Constellations AI, our focus is on the architecture layer that enables agents to collaborate, adapt, and act intelligently across domains.
            </p>
            
            <p className="text-lg text-muted-foreground leading-relaxed">
              Whether deploying market agents with human-inspired trading strategies, digital twins in secure air-gapped environments, or simulation agents generating mission-ready courses of action—our orchestration systems ensure each agent integrates with the larger mission in real time.
            </p>
            
            <p className="text-lg text-muted-foreground leading-relaxed">
              Our core stack combines fine-tuned language models with graph-structured memory and real-time reasoning to create orchestration frameworks that evolve with complexity, enabling AI to mirror human decision-making at machine speed.
            </p>
            
            <p className="text-lg text-muted-foreground leading-relaxed">
              At Constellations AI, we design systems that complement human ingenuity. We don't engineer mere tools, we create AI partners—working alongside humanity to explore, create, and achieve the impossible.
            </p>
            
            <div className="pt-8">
              <h3 className="text-2xl font-bold text-foreground mb-6">Portfolio</h3>
              <div className="flex flex-wrap justify-center gap-4">
                {projects.map((project, index) => (
                  project.status === "active" ? (
                    <Dialog key={index}>
                      <DialogTrigger asChild>
                        <Badge 
                          variant="secondary" 
                          className="px-4 py-2 text-stellar bg-stellar/20 border-stellar/40 cursor-pointer hover:bg-stellar/30 hover:border-stellar/60 transition-all duration-300"
                        >
                          {project.title}
                        </Badge>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl bg-card/95 backdrop-blur-sm border-stellar/40">
                        <DialogHeader>
                          <DialogTitle className="text-stellar text-2xl">{project.title}</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="text-muted-foreground leading-relaxed">
                            {Array.isArray(project.description) 
                              ? project.description.map((paragraph, idx) => (
                                  <p key={idx} className="mb-4 last:mb-0">{paragraph}</p>
                                ))
                              : <p>{project.description}</p>
                            }
                          </div>
                          <div className="flex gap-4 pt-4">
                            <Button 
                              className="bg-stellar hover:bg-stellar-glow text-white"
                              onClick={() => window.open(project.link, '_blank')}
                            >
                              Launch Application
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  ) : (
                    <Dialog key={index}>
                      <DialogTrigger asChild>
                        <Badge 
                          variant="secondary" 
                          className="px-4 py-2 text-muted-foreground bg-muted/20 border-muted/40 cursor-pointer hover:bg-muted/30 hover:border-muted/50 opacity-50 hover:opacity-75 transition-all duration-300"
                        >
                          {project.title}
                        </Badge>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl bg-card/95 backdrop-blur-sm border-muted/40">
                        <DialogHeader>
                          <DialogTitle className="text-foreground text-2xl">{project.title}</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div className="flex items-center gap-2 mb-4">
                            <Badge className="bg-cosmic text-foreground">Coming Soon</Badge>
                          </div>
                          <div className="text-muted-foreground leading-relaxed">
                            {Array.isArray(project.description) 
                              ? project.description.map((paragraph, idx) => (
                                  <p key={idx} className="mb-4 last:mb-0">{paragraph}</p>
                                ))
                              : <p>{project.description}</p>
                            }
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>
                  )
                ))}
              </div>
            </div>
          </div>
          
          <div className="pt-12">
            <Button 
              size="lg" 
              className="bg-stellar hover:bg-stellar-glow text-white px-8 py-3 text-lg font-medium shadow-[0_0_30px_hsl(var(--stellar)_/_0.4)] hover:shadow-[0_0_50px_hsl(var(--stellar-glow)_/_0.6)] transition-all duration-500"
              onClick={() => document.getElementById('chief-architect')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Meet Our Chief Architect
            </Button>
          </div>
        </div>
        
        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-stellar/60 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-stellar rounded-full mt-2 animate-stellar-pulse"></div>
          </div>
        </div>
      </section>

      {/* Chief Architect Section */}
      <section id="chief-architect" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-stellar to-nebula bg-clip-text text-transparent">
              Chief Architect
            </h2>
            <div className="h-1 w-24 bg-gradient-to-r from-stellar to-nebula mx-auto mb-6"></div>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Meet the visionary leader driving our technological innovation and architectural excellence.
            </p>
          </div>

          {/* Biography Card */}
          <Card className="mb-16 p-8 bg-card/80 backdrop-blur-sm border-stellar/20 hover:border-stellar/40 transition-all duration-500">
            <div className="grid md:grid-cols-3 gap-8 items-start">
              <div className="md:col-span-1">
                <div className="relative">
                  <img 
                    src={headshot} 
                    alt="Chief Architect" 
                    className="w-full max-w-sm mx-auto rounded-full aspect-square object-cover object-[center_top_-0.5in] shadow-[0_0_30px_hsl(var(--stellar)_/_0.3)] hover:shadow-[0_0_50px_hsl(var(--stellar-glow)_/_0.4)] transition-all duration-500"
                    style={{ objectPosition: 'center 20%' }}
                  />
                  <div className="absolute inset-0 rounded-full bg-gradient-to-t from-stellar/20 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-500"></div>
                </div>
              </div>
              
              <div className="md:col-span-2 space-y-6">
                <div>
                  <h3 className="text-3xl font-bold text-foreground mb-2">Dr. Joanne Lo</h3>
                  <p className="text-xl text-stellar font-medium mb-4">Chief Architect</p>
                  
                  <div className="flex flex-wrap gap-2 mb-6">
                    <Badge className="bg-cosmic text-foreground">Ph.D. Electrical Engineering and Computer Sciences</Badge>
                    <Badge className="bg-cosmic text-foreground">UC Berkeley '16</Badge>
                    <Badge className="bg-cosmic text-foreground">16+ Years Experience</Badge>
                  </div>
                </div>
                
                <div className="space-y-4 text-muted-foreground leading-relaxed">
                  <p>
                    Dr. Joanne Lo is a visionary technologist and seasoned executive known for architecting intelligent systems at the intersection of defense, AI, and human-centered design. With over 16 years of leadership spanning government, academia, and industry, she brings a rare blend of deep technical expertise and strategic foresight to Constellations AI.
                  </p>
                  
                  <p>
                    Prior to founding Constellations AI, Dr. Lo served as the Chief Technology Officer of Special Operations Command, Pacific (SOCPAC), where she led the U.S. Special Operations Indo-Pacific Tech Strategy. Her work modernized digital infrastructure and deployed autonomous systems that enhanced the safety and mission readiness of U.S. and allied forces operating in contested environments.
                  </p>
                  
                  <p>
                    Dr. Lo's research spans from the atomic to the strategic—with publications and patents ranging from device physics and human-computer interaction to military science and national strategy. This unique perspective allows her to architect systems that are both technically rigorous and operationally relevant. Throughout her career, she has pushed the boundaries of human potential—not only by engineering systems stress-tested in the world's most volatile domains, but by shaping national strategies for AI education, deployment, and safety.
                  </p>
                  
                  <p>
                    While serving in senior military leadership, Dr. Lo embodied a core belief: that national resilience begins with building resilience at home. At Constellations AI, her mission is to reimagine the technological foundations of our society—one system, one policy, one human-machine relationship at a time.
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Professional Timeline */}
          <div>
            <h3 className="text-3xl font-bold text-center mb-12 text-foreground">
              Professional Journey
            </h3>
            <Timeline />
          </div>
        </div>
      </section>
    </div>
  );
};

export default LandingPage;