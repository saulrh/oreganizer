# Oreganizer

A bug-tracker-like system like JIRA or Github Issues, but for Minecraft. Write down what you want to do, estimate how long each will take, specify dependencies, and oreganizer will figure out how to do things efficiently and help you schedule it all.

# Example setup:

* Kill the ender dragon
  * Consumables:
    * Regen Potion (4x)
  * Infrastructure:
    * TiC Crossbow
    * Flux Jetplate
    * Flux Head, Legs, Feet
* Regen Potion
  * Consumables:
    * Ghast Tear (1x)
    * Nether Wart (1x)
  * Infrastructure:
    * Brewing Stand
* Ghast Tear
  * Consumables:
  * Infrastructure:
    * Bow
    * Nether Portal
    * Find Nether Fortress
* Nether Wart
  * Consumables:
  * Infrastructure:
    * Nether Portal
* Nether Portal
  * Consumables:
    * Obsidian (10x)
  * Infrastructure:
    * Obsidian-level TiC Pick
* TiC Crossbow
  * Consumables:
    * Slime Crossbow Limb (1x)
    * Thaumium Body (1x)
    * Paper Tough Binding (1x)
    * Fiery Bowstring (1x)
  * Infrastructure:
    * Tool Forge

And so on. Oreganizer will take this and convert it to a comprehensible, ordered list of tasks optimized for doing things simultaneously and and efficiently. Oreganizer will do a recursive descent of the system to figure out all the resources necessary. Consumables are consumed per "use", while infrastructure you only need one of. you can add times, and if a task is expected to take an infeasible amount of time oreganizer will warn you about it and make a recommendation about which part of the process to optimize or accelerate. the system scans a directory for task files and considers all of them; this lets you do things like split your oreganizer files up by mod or megaproject, put them in revision control, or share them with other people (got a nice, comprehensive task list for applied energistics? post it somewhere for everyboyd else!).
