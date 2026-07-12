# 🐧 90 Days to Your First Kernel Patch

> A checkable, resume-anytime plan: from "I have a working KVM lab" to submitting real
> patches to the Linux kernel. Twelve weeks · three phases · mixed reading / video /
> free courses / hands-on.
>
> **Interactive version** (progress saves in your browser, exports back to this file):
> https://mrdee.in/kernel-plan/

Tick a box with `[x]` and add the date you finished it — e.g. `- [x] (2026-07-12) ...`.
The web tracker stamps these automatically and can re-export this file for you.

---

## ⟲ Fell off the wagon? Read this, not the guilt.

- **Don't restart the clock — resume the checkbox.** Missing days is expected; this plan
  is built to be re-entered, not perfected. Your progress only ever goes up.
- **The 15-minute rule.** On a low-energy day, do one `git pull && make`-sized thing:
  read one doc section, watch 10 min, or tick one task. Momentum beats intensity.
- **Been away a week+?** Jump to the *last unchecked box* — don't re-read what's done.

---

## Phase 01 · Days 1–30 · Foundations
*Get fluent at the command line, refresh C, master git, and build + boot your first kernel in the VM you already have.*

### Week 1 — Command-line & environment fluency
- [ ] `COURSE` Audit LFS101 Introduction to Linux — chapters 1–6
- [ ] `BUILD`  Live in the shell: pipes, grep, find, ps, top, systemctl, journalctl — no GUI for a day
- [ ] `READ`   Skim `man` for 10 core tools; write yourself a one-page cheat sheet
- [ ] `BUILD`  Set up tmux + your editor the way you'll use it for 90 days

### Week 2 — C refresh for kernel work
- [ ] `READ`   Refresh pointers, structs, bitwise ops, function pointers
- [ ] `BUILD`  Write 3 small C programs: a linked list, a bitmask flag parser, a string tokenizer
- [ ] `READ`   Read `Documentation/process/coding-style.rst`
- [ ] `BUILD`  Compile with `gcc -Wall -Wextra`; fix every warning

### Week 3 — Git & the patch mindset
- [ ] `COURSE` Start LFD102 — open source etiquette & licensing
- [ ] `BUILD`  Practice: branch, commit, rebase -i, format-patch, send-email (to yourself)
- [ ] `READ`   Read 20 real kernel commits with `git log` — study the message style
- [ ] `BUILD`  Clone mainline: `git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`

### Week 4 — Build & boot your first kernel
- [ ] `BUILD`  `make defconfig` → `nice -n 19 make` → `~/kernel-vm/boot.sh arch/x86/boot/bzImage`
- [ ] `BUILD`  Change `CONFIG_LOCALVERSION`, rebuild, confirm the new `uname -r` in the VM
- [ ] `READ`   Read `Documentation/admin-guide/README.rst` and kbuild basics
- [ ] `BUILD`  Break something on purpose, read the failure, fix it — learn the loop

---

## Phase 02 · Days 31–60 · Kernel internals & reading code
*Understand how the kernel is put together, write loadable modules, and get comfortable reading unfamiliar subsystem code.*

### Week 5 — LFD103 + the big picture
- [ ] `COURSE` Work through LFD103 — modules 1–4
- [ ] `READ`   Robert Love, *Linux Kernel Development* — ch. 1–3
- [ ] `WATCH`  Watch one kernel-internals overview lecture end to end

### Week 6 — Write kernel modules
- [ ] `READ`   Follow the Kernel Module Programming Guide — hello world → char device
- [ ] `BUILD`  Build & `insmod` a module in the VM; watch it in `dmesg`
- [ ] `BUILD`  Write a module exposing a `/proc` or `sysfs` entry you can read/write
- [ ] `READ`   LFD103 modules 5–7

### Week 7 — Reading real subsystem code
- [ ] `READ`   Pick ONE subsystem (e.g. a `drivers/staging/` driver) and read it top to bottom
- [ ] `BUILD`  Use `cscope`/`ctags` or LXR to trace a function call chain
- [ ] `READ`   Love book ch. 4–5 (scheduling, syscalls); an LWN article on the same area
- [ ] `BUILD`  Add a `printk` to a real code path, rebuild, boot, watch it fire

### Week 8 — Debugging & tooling
- [ ] `BUILD`  Trigger and read a kernel oops in the VM; decode the stack trace
- [ ] `BUILD`  Run `scripts/checkpatch.pl --strict` on a random file — read what it flags
- [ ] `READ`   Learn `ftrace` / `dmesg` / `gdb`-on-qemu basics
- [ ] `READ`   Read `Documentation/process/submitting-patches.rst` fully

---

## Phase 03 · Days 61–90 · Your first contribution
*Find a real, small, legitimate fix; produce a clean patch; send it to the right maintainers; survive and act on review.*

### Week 9 — Find your first target
- [ ] `READ`   Do the KernelNewbies First Kernel Patch tutorial start to finish
- [ ] `BUILD`  Hunt in `drivers/staging/` with checkpatch for a genuine style/sparse fix
- [ ] `BUILD`  Use `scripts/get_maintainer.pl` to find who + which list your change goes to
- [ ] `WATCH`  Watch GKH: Write & Submit Your First Patch

### Week 10 — Craft the patch
- [ ] `BUILD`  Make the change; build clean; test it boots in your VM
- [ ] `BUILD`  `git commit` with a proper message + `Signed-off-by`; run checkpatch until silent
- [ ] `BUILD`  `git format-patch`; configure `git send-email` with your SMTP
- [ ] `BUILD`  Send the patch to YOURSELF first; confirm it applies with `git am`

### Week 11 — Submit & engage
- [ ] `BUILD`  Send the patch to the maintainer + list, CC as get_maintainer says
- [ ] `READ`   Subscribe to the mailing list; read a week of traffic to learn the tone
- [ ] `BUILD`  Respond to review feedback promptly and politely; send a v2 with a changelog

### Week 12 — Iterate & keep going
- [ ] `BUILD`  Land it (or keep iterating) — then find a second, slightly harder fix
- [ ] `READ`   Write a short note-to-self: what surprised you, what you'd do faster next time
- [ ] `READ`   Scope a longer path: Outreachy / GSoC, or adopt a staging driver
- [ ] `BUILD`  Set a sustainable cadence (one patch / fortnight) so month 4 isn't a cliff

---

## 📚 Reference shelf (all free unless marked)

**Free courses**
- LFD103 — A Beginner's Guide to Linux Kernel Development *(the spine of this plan)* — https://training.linuxfoundation.org/training/a-beginners-guide-to-linux-kernel-development-lfd103/
- LFS101 — Introduction to Linux *(free audit on edX)* — https://training.linuxfoundation.org/training/introduction-to-linux-lfs101x/
- LFD102 — A Beginner's Guide to Open Source Software Development — https://training.linuxfoundation.org/training/a-beginners-guide-to-open-source-software-development-lfd102/

**Books**
- *Linux Kernel Development* — Robert Love *(readable starting book, paid)*
- Linux Device Drivers, 3rd ed (LDD3) *(free PDF)* — https://lwn.net/Kernel/LDD3/
- The Linux Kernel Module Programming Guide *(free, kept current)* — https://sysprog21.github.io/lkmpg/

**Docs & sites**
- KernelNewbies — First Kernel Patch — https://kernelnewbies.org/FirstKernelPatch
- kernel.org — Development Process docs — https://docs.kernel.org/process/index.html
- Bootlin free training materials — https://bootlin.com/docs/
- LWN Kernel Index — https://lwn.net/Kernel/Index/

**Video**
- GKH — Write & Submit Your First Patch (search YouTube for Greg Kroah-Hartman)

**Where to contribute**
- Kernel Janitors (small cleanup tasks) — https://kernelnewbies.org/KernelJanitors
- `drivers/staging/` tree *(friendliest first-patch target)*
- Outreachy — https://www.outreachy.org/ · GSoC — https://summerofcode.withgoogle.com/

**Your lab (already set up)**
- trixie 13.6 · KVM + libvirt working
- `~/kernel-vm/boot.sh` — boot any bzImage
- `nice -n 19 make` — your build command
- `scripts/checkpatch.pl` — run before every patch

---

## 🗓️ Check-in log
*Newest first. The web tracker appends a timestamped line here each session you export; you can also add your own.*

<!-- CHECKINS -->
- _(no check-ins yet — tick a task in the tracker, then Download to fill this in)_
