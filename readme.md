# Oreganizer

An issue tracker optimized for Minecraft. Write down what you want to do, estimate how long each will take, specify dependencies, and oreganizer will figure out how to do things efficiently and help you schedule it all. Building an issue tracker specifical for Minecraft bakes in some assumptions about machines, consumables, and scheduling that make it "Do the right thing" enough for it to be more useful than, say, org-mode.

# Example setup:

* Kill ender dragon
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
* Brewing Stand
  * Consumables:
    * Blaze Rod (1x)
  * Infrastructure:
* Blaze Rod
  * Consumables:
  * Infrastructure:
    * Find Nether Fortress
* Ghast Tear
  * Consumables:
  * Infrastructure:
    * Nether Portal
* Nether Wart
  * Consumables:
  * Infrastructure:
    * Nether Portal
    * Find Nether Fortress
* Nether Portal
  * Consumables:
    * Obsidian (10x)
  * Infrastructure:
    * Obsidian-level TiC Pick
* Find Nether Fortress
  * Consumables:
  * Infrastructure:
    * Nether Portal

And so on. Oreganizer will take this and convert it to an immediately-executable ordered list of tasks optimized for doing things simultaneously and efficiently:

1. Nether Portal
2. Ghast Tear (4x)
3. Find Nether Fortress
4. Nether Wart (4x)
5. Blaze Rod
6. Brewing Stand using Blaze Rod
7. Regen Potion (4x) using Nether Warts and Ghast Tears
8. [...]
9. Kill Ender Dragon

Oreganizer will do a recursive descent of the system to figure out all the resources necessary. Consumables are consumed per "use", while infrastructure you only need one of. you can add times, and if a task is expected to take an infeasible amount of time oreganizer will warn you about it and make a recommendation about which part of the process to optimize or accelerate. the system scans a directory for task files and considers all of them; this lets you do things like split your oreganizer files up by mod or megaproject, put them in revision control, or share them with other people (got a nice, comprehensive task list for applied energistics? post it somewhere for everyboyd else!).
