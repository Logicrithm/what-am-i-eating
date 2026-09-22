# What this dataset still cannot tell a person

Written from the point of view of someone standing in a shop holding a packet.
These are the honest gaps. They are listed here rather than quietly ignored.

---

## 1. A limit in the rules is not a dose in your body

FSSAI limits are written as **milligrams per kilogram of food**. Nobody eats a
kilogram. People eat a 70 g packet.

We hold the limits, so this is computable: *"a 70 g packet of this could legally
contain up to X mg."* That single translation turns a regulation into something a
person can picture. Not built yet.

## 2. The safe limit depends on body weight, and children are lighter

Acceptable daily intake is **per kilogram of body weight per day**. A 20 kg child
and a 65 kg adult eating the same packet are not having the same experience - the
child receives roughly three times the dose per kilogram.

This is not speculation. EFSA has already measured European children and toddlers
exceeding the limit on average for sodium benzoate, carrageenan, diphosphates and
calcium phosphates - all of which are common in Indian packaged food.

We do not yet ask for body weight or portion size, so we cannot say this to the
person it most concerns.

## 3. One packet is not the question - partly answered now

The real exposure comes from biscuits plus noodles plus sauce plus a soft drink,
all carrying the same additive on the same day.

"My day" now holds the labels a reader has looked at and shows what repeats
across them, because a daily limit applies to everything eaten in a day rather
than to one packet. The list lives in that browser only and is never sent
anywhere.

What it still cannot do is add the amounts up. That would need the portion eaten
of each item, and the label never states how much additive was actually used - so
any total would be a guess dressed as arithmetic. It names the repetition and
stops there. Only 10 of our 100 additives even have a published daily limit to
measure a total against.

## 4. Some people need a different answer from everyone else

A general "safe for the population" figure is not an answer for:

- people with asthma, for sulphites
- people sensitive to aspirin, for certain azo colours
- people with phenylketonuria, for aspartame
- pregnant people, infants, the elderly

Some of these already require warnings on Indian labels. None of it is in our
cards yet, and a card that ignores it is giving a healthy adult's answer to
someone who is not a healthy adult.

## 5. Sometimes the label may stay general - and sometimes it should not have

From our own count of real Indian products:

| What the label leaves general | Share of products |
|---|---|
| just "flavouring" (permitted) | 7.8% |
| just "acidity regulator" (**rule asks for the name or INS number**) | 7.0% |
| just "vegetable oil" (**rule asks for the specific oil**) | 6.8% |
| just "emulsifier" (**rule asks for the name or INS number**) | 6.2% |
| just "spices" (permitted) | 4.8% |

An earlier version of this file published these as 26%, 20%, 20% and 19%. Those
numbers were wrong: Open Food Facts tags are hierarchical, so a product saying
"palm oil" also carries the parent tag "vegetable oil", and counting the parent
counted products that HAD named their oil. We were overstating how much labels
hide. Corrected 2026-09-21.

The bigger correction is what it means. This section used to say the label is not
required to tell you. For some of these that is true - spices, condiments and
flavourings may use a class title. For others it is the opposite: the Labelling
and Display Regulations 2020 require a specific name, and the entry for edible
vegetable oil reads "Give name of the specific edible oil such as mustard oil,
groundnut oil, etc." Functional additive classes must carry the specific name or
the INS number.

So the useful thing to show is not one message but two: where a general word is
all the rule requires, and where the rule asks for more than the label gave. The
site now separates them.

## 6. The label also never tells you how much was actually used

Manufacturers must stay under the maximum. They do not have to declare what they
actually used. So "contains INS 211" could mean a trace or could mean the legal
ceiling, and nothing on the packet distinguishes them.

## 7. Vegetarian is not a settled question

Nine of India's fifty most common additives can be made from either plant or
animal sources - lecithin, mono- and diglycerides, disodium inosinate, glycerol
and others. The label is not required to say which source was used, and a pack can
still carry the green dot.

This is now recorded on every card. It may be the single most India-specific thing
in the whole dataset.

## 8. Cooking changes things

Some additives behave differently once heated, fried or reheated - which is most
of how this food is actually eaten. Nothing in our sources covers that.

## 9. Who produced the evidence, and who paid for it

A fair question, and it deserves a straight answer rather than either a shrug or
an accusation.

Safety evaluations often rest on studies submitted by the companies that want the
substance approved. That is how the system is built worldwide, and it is a real
reason for caution. It is also not the same thing as proof of corruption, and this
project will not claim otherwise without evidence.

What we can do instead of picking a side is make the provenance visible:

- **who** decided, and under which law
- **when** they decided - 10 of our 50 rest on EU opinions 12 or more years old.
  Tartrazine's is from 2010. And citric acid, the single most common additive in
  Indian packaged food, has no EU food-additive opinion we could find at all.
- **whether regulators disagree** - none of the top 50 currently do. But that is
  a weaker statement than it sounds: only 15 of the 50 cards carry all three
  authorities, so the comparison is genuinely tested on 15. On the rest we are
  missing India, the EU or the US and simply do not know. Each card now says how
  many of the three it was tested against.
- **the full document**, linked, so nobody has to take our word for it

Transparency about provenance is the honest response to distrust. Manufactured
suspicion is not.

## 10. The same substance appears more than once

INS numbers come in families. 500 is the sodium carbonates group, 500(i) is
sodium carbonate, 500(ii) is baking soda. Our fifty cards therefore cover 42
distinct substances, not 50, and a search can turn up what looks like two
answers for one thing.

Merging them would be wrong - 150(a) and 150(d) are different caramels, and only
150(d) carries sulphites. So each card now names its siblings instead.

## 11. Absence of evidence is not safety

"No safety concern identified" usually means nobody found a problem in the studies
that were done. Long-term, low-dose, lifelong, mixed-with-everything-else exposure
is genuinely not well studied for most additives.

The cards should say that plainly where it is true, rather than letting a clean
regulatory status imply more certainty than exists.
