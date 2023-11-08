#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
The intent of this map is to be able to a single canonical author
for every ``Name <email>`` combination.
"""

__all__ = (
    "canonical_author_map",
)

from typing import (
    Dict,
)


def canonical_author_map() -> Dict[str, str]:
    """
    Return a map of authors to their canonical author & email.
    """
    # NOTE:
    # - Keys must be ordered,
    # - Values must also be ordered.
    author_map_valid_to_invalid = {
        "Aaron Carlisle <carlisle.aaron00@gmail.com>": (
            "Aaron <Aaron>",
            "Aaron <carlisle.b3d@gmail.com>",
            "Aaron Carlisle <Blendify>",
            "Aaron Carlisle <blendify@noreply.localhost>",
            "Aaron Carlisle <carlisle.b3d@gmail.com>",
            "Your Name <Aaron Carlisle>",
        ),
        "Alan Troth <Al>": (
            "Alan <Al@AlanTroth.me.uk>",
        ),
        "Alaska <alaskayou01@gmail.com>": (
            "Alaska <Alaska>",
            "Alaska <alaska@noreply.localhost>",
        ),
        "Aleksandr Zinovev <roaoao@gmail.com>": (
            "raa <roaoao@gmail.com>",
        ),
        "Alexander Gavrilov <angavrilov@gmail.com>": (
            "Alexander Gavrilov <alexander.gavrilov@jetbrains.com>",
        ),
        "Alexander Romanov <a.romanov@blend4web.com>": (
            "Romanov Alexander <a.romanov@blend4web.com>",
        ),
        "Alexandr Kuznetsov <ak3636@nyu.edu>": (
            "Alexandr Kuznetsov <kuzsasha@gmail.com>",
        ),
        "Aleš Jelovčan <frogstomp>": (
            "frogstomp <email.frogstomp@gmail.com>",
        ),
        "Almaz Shinbay <almaz.shinbay@nu.edu.kz>": (
            "Almaz-Shinbay <almaz-shinbay@noreply.localhost>",
        ),
        "Amélie Fondevilla <amelie.fondevilla@les-fees-speciales.coop>": (
            "Amelie <amelie.fondevilla@les-fees-speciales.coop>",
            "Amelie Fondevilla <afonde>",
            "Amelie Fondevilla <amelie.fondevilla@les-fees-speciales.coop>",
            "Amelie Fondevilla <amelie@les-fees-speciales.coop>",
            "Amelie Fondevilla <amelief@noreply.localhost>",
            "Amélie Fondevilla <afonde>",
        ),
        "Andrii Symkin <pembem22>": (
            "Andrii <pembem22>",
            "pembem22 <pembem22>",
        ),
        "Ankit Meel <ankitjmeel@gmail.com>": (
            "Ankit <ankitm>",
            "Ankit Meel <ankitm>",
        ),
        "Anthony Edlin <akrashe@gmail.com>": (
            "Anthony Edlin <krash>",
        ),
        "Anthony Roberts <anthony.roberts@linaro.org>": (
            "Anthony <anthony-roberts@noreply.localhost>",
        ),
        "Antonio Vazquez <blendergit@gmail.com>": (
            "Antonio  Vazquez <blendergit@gmail.com>",
            "Antonio Vazquez <antoniov>",
            "Antonio Vazquez <antoniov@noreply.localhost>",
            "Antonioya <blendergit@gmail.com>",
        ),
        "Antony Riakiotakis <kalast@gmail.com>": (
            "Antony Ryakiotakis <kalast@gmail.com>",
        ),
        "Aras Pranckevicius <aras@nesnausk.org>": (
            "Aras Pranckevicius <aras_p>",
        ),
        "Arye Ramaty <aryeramaty@gmail.com>": (
            "Arye Ramaty <BelgaratTheGrey>",
        ),
        "Bastien Montagne <bastien@blender.org>": (
            "Bastien Montagne (@mont29) <>",
            "Bastien Montagne <b.mont29@gmail.com>",
            "Bastien Montagne <mont29>",
            "Bastien Montagne <montagne29@wanadoo.fr>",
            "bastien <bastien@blender.org>",
            "mont29 <montagne29@wanadoo.fr>",
        ),
        "Bogdan Nagirniak <bodyan@gmail.com>": (
            "Bogdan Nagirniak <bnagirniak>",
        ),
        "Brecht Van Lommel <brecht@blender.org>": (
            "Brecht Van Lommel <brecht>",
            "Brecht Van Lommel <brecht@noreply.localhost>",
            "Brecht Van Lommel <brecht@solidangle.com>",
            "Brecht Van Lommel <brechtvanlommel@gmail.com>",
            "Brecht Van Lommel <brechtvanlommel@pandora.be>",
            "Brecht Van Lömmel <brechtvanlommel@gmail.com>",
            "Brecht van Lommel <brechtvanlommel@gmail.com>",
            "recht Van Lommel <brecht@blender.org>",
        ),
        "Brendon Murphy <meta.androcto1@gmail.com>": (
            "meta-androcto <meta.androcto1@gmail.com>",
        ),
        "Brian Savery <brian.savery@gmail.com>": (
            "Brian Savery (AMD) <briansavery@noreply.localhost>",
            "Brian Savery <bsavery>",
            "bsavery <brian.savery@gmail.com>",
        ),
        "Campbell Barton <campbell@blender.org>": (
            "Campbell Barton <campbellbarton>",
            "Campbell Barton <ideasman42@gmail.com>",
        ),
        "Casey Bianco-Davis <caseycasey739@gmail.com>": (
            "casey bianco-davis <caseycasey739@gmail.com>",
        ),
        "Charles Wardlaw <cwardlaw@nvidia.com>": (
            "Charles Wardlaw (@CharlesWardlaw) <>",
            "Charles Wardlaw <charleswardlaw@noreply.localhost>",
            "Charles Wardlaw <kattkieru@users.noreply.github.com>",
        ),
        "Charlie Jolly <mistajolly@gmail.com>": (
            "Charlie Jolly <charlie>",
            "charlie <mistajolly@gmail.com>",
        ),
        "Christian Brinkmann <hallo@zblur.de>": (
            "christian brinkmann <>",
        ),
        "Christian Rauch <Rauch.Christian@gmx.de>": (
            "Christian Rauch <christian.rauch>",
        ),
        "Christoph Lendenfeld <chris.lenden@gmail.com>": (
            "Christoph Lendenfeld <ChrisLend>",
            "Christoph Lendenfeld <chris.lend@gmx.at>",
            "Christoph Lendenfeld <chrislend@noreply.localhost>",
        ),
        "Clément Foucault <foucault.clem@gmail.com>": (
            "Clment Foucault <fclem>",
            "Clment Foucault <foucault.clem@gmail.com>",
            "ClÃ©ment Foucault <foucault.clem@gmail.com>",
            "Clément <clement@Clements-MacBook-Pro.local>",
            "Clément Foucault <fclem>",
            "Clément Foucault <fclem@noreply.localhost>",
            "fclem <foucault.clem@gmail.com>",
        ),
        "Colin Basnett <cmbasnett@gmail.com>": (
            "Colin Basnett <cmbasnett>",
            "Colin Basnett <cmbasnett@noreply.localhost>",
        ),
        "Colin Marmond <kdblender@gmail.com>": (
            "Colin <Kdaf>",
            "Colin Marmond <Kdaf>",
            "Colin Marmond <kdaf@noreply.localhost>",
            "Colin Marmont <Kdaf>",
        ),
        "Dalai Felinto <dalai@blender.org>": (
            "Dalai Felinto <dfelinto>",
            "Dalai Felinto <dfelinto@gmail.com>",
            "Dalai Felinto <dfelinto@noreply.localhost>",
        ),
        "Damien Picard <dam.pic@free.fr>": (
            "Damien Picard <pioverfour>",
            "Damien Picard <pioverfour@noreply.localhost>",
        ),
        "Daniel Salazar <zanqdo@gmail.com>": (
            "Daniel Salazar <zanqdo>",
            "Daniel Salazar <zanqdo@noreply.localhost>",
            "Daniel Santana <dgsantana>",
            "ZanQdo <zanqdo@gmail.com>",
            "zanqdo <zanqdo@gmail.com>",
        ),
        "David Friedli <hlorus>": (
            "David <hlorus>",
        ),
        "Demeter Dzadik <Mets>": (
            "demeterdzadik@gmail.com <demeterdzadik@gmail.com>",
        ),
        "Diego Borghetti <bdiego@gmail.com>": (
            "Diego Hernan Borghetti <bdiego@gmail.com>",
        ),
        "Dilith Jayakody <dilithjay@gmail.com>": (
            "dilithjay <dilithjay@gmail.com>",
        ),
        "Dmitry Dygalo <noreply@developer.blender.org>": (
            "Dmitry Dygalo <>",
        ),
        "Dontsov Valentin <@blend4web.com>": (
            "Dotsnov Valentin <invalid@nodomain.com>",
        ),
        "EitanSomething <eitant13@gmail.com>": (
            "Eitan <EitanSomething>",
            "EitanSomething <EitanSomething>",
        ),
        "Ejner Fergo <ejnersan@gmail.com>": (
            "Ejner Fergo <ejnersan>",
        ),
        "Erik Abrahamsson <ecke101@gmail.com>": (
            "Eric Abrahamsson <ecke101@gmail.com>",
            "Erick Abrahammson <ecke101@gmail.com>",
            "Erik <ecke101@gmail.com>",
            "Erik Abrahamsson <erik85>",
            "Erik Abrahamsson <erik85@noreply.localhost>",
        ),
        "Ethan Hall <Ethan1080>": (
            "Ethan-Hall <Ethan1080>",
        ),
        "Fabian Schempp <fabianschempp@googlemail.com>": (
            "Fabian Schempp <fabian_schempp>",
        ),
        "Falk David <falk@blender.org>": (
            "Falk David <falkdavid@gmx.de>",
            "Falk David <filedescriptor>",
            "Falk David <filedescriptor@noreply.localhost>",
            "filedescriptor <falkdavid@gmx.de>",
        ),
        "Francesco Siddi <francesco@blender.org>": (
            "Francesco Siddi <francesco.siddi@gmail.com>",
            "Francesco Siddi <fsiddi>",
        ),
        "Fynn Grotehans <fynngr@noreply.localhost>": (
            "Fynn Grotehans <68659993+Fynn-G@users.noreply.github.com>",
            "Fynn Grotehans <TheFynn>",
        ),
        "Félix <Miadim>": (
            "Flix <Miadim>",
        ),
        "Gaia Clary <gaia.clary@machinimatrix.org>": (
            "Gaia Clary <gaiaclary>",
            "gaiaclary <gaia.clary@machinimatrix.org>",
        ),
        "Georgiy Markelov <georgiy.m.markelov@gmail.com>": (
            "georgiy.m.markelov@gmail.com <georgiy.m.markelov@gmail.com>",
        ),
        "Germano Cavalcante <germano.costa@ig.com.br>": (
            "Germano <germano.costa@ig.com.br>",
            "Germano Cavalcante <grmncv@gmail.com>",
            "Germano Cavalcante <mano-wii>",
            "Germano Cavalcante <mano-wii@noreply.localhost>",
            "Germano Cavalcantemano-wii <germano.costa@ig.com.br>",
            "mano-wii <germano.costa@ig.com.br>",
            "mano-wii <grmncv@gmail.com>",
        ),
        "Gilberto Rodrigues <gilbertorodrigues@outlook.com>": (
            "Gilberto Rodrigues <gilberto_rodrigues>",
        ),
        "Guillermo S. Romero <gsr.b3d@infernal-iceberg.com>": (
            "gsr b3d <gsr.b3d@infernal-iceberg.com>",
        ),
        "Guillermo Venegas <guillermovcra@gmail.com>": (
            "Guillermo <guillermovcra@gmail.com>",
            "guishe <guillermovcra@gmail.com>",
        ),
        "Habib Gahbiche <habibgahbiche@gmail.com>": (
            "Habib Gahbiche <zazizizou>",
        ),
        "Hans Goudey <hans@blender.org>": (
            "Hans Goudey <HooglyBoogly>",
            "Hans Goudey <h.goudey@me.com>",
            "Hans Goudey <hooglyboogly@noreply.localhost>",
        ),
        "Harley Acheson <harley.acheson@gmail.com>": (
            "Harley Acheson <harley>",
            "Harley Acheson <harley@noreply.localhost>",
        ),
        "Henrik Dick <hen-di@web.de>": (
            "Henrik Dick (weasel) <>",
            "Henrik Dick <weasel>",
        ),
        "Himanshi Kalra <himanshikalra98@gmail.com>": (
            "Himanshi Kalra <calra>",
        ),
        "Howard Trickey <howard.trickey@gmail.com>": (
            "howardt <howard.trickey@gmail.com>",
        ),
        "Hristo Gueorguiev <prem.nirved@gmail.com>": (
            "Hristo Gueorguiev <>",
        ),
        "IRIE Shinsuke <irieshinsuke@yahoo.co.jp>": (
            "Irie Shinsuke <irieshinsuke@yahoo.co.jp>",
        ),
        "Iliya Katueshenock <modormoder@gmail.com>": (
            "Iliay Katueshenock <Moder>",
            "Iliya Katueshenock <Moder>",
            "Iliya Katueshenock <mod_moder@noreply.localhost>",
            "MOD <Moder>",
            "illua1 <modormoder@gmail.com>",
        ),
        "Inês Almeida <britalmeida@gmail.com>": (
            "Ines Almeida <britalmeida@gmail.com>",
            "brita <britalmeida@gmail.com>",
        ),
        "Ish Bosamiya <ish_bosamiya>": (
            "Ish Bosamiya <ishbosamiya>",
            "Ish Bosamiya <ishbosamiya@gmail.com>",
        ),
        "Ivan Kosarev <mail@ivankosarev.com>": (
            "kosarev <kosarev@noreply.localhost>",
        ),
        "Iyad Ahmed <iyadahmed430@gmail.com>": (
            "Iyad Ahmed <iyadahmed2001>",
        ),
        "Jacques Lucke <jacques@blender.org>": (
            "Jacques Lucke <jacqueslucke@noreply.localhost>",
            "Jacques Lucke <mail@jlucke.com>",
        ),
        "Jason Fielder <jason-fielder@noreply.localhost>": (
            "Jason Fielder <jason_apple>",
        ),
        "Jens Ole Wund <bjornmose@gmx.net>": (
            "bjornmose <bjornmose@gmx.net>",
        ),
        "Jens Verwiebe <info@jensverwiebe.de>": (
            "Jens <info@jensverwiebe.de>",
            "Jens Verwiebe <jensverwiebe@jens-macpro.fritz.box>",
            "jensverwiebe <info@jensverwiebe.de>",
        ),
        "Jeroen Bakker <jeroen@blender.org>": (
            "Jeroen Bakker <88891617+jeroen-blender@users.noreply.github.com>",
            "Jeroen Bakker <j.bakker@atmind.nl>",
            "Jeroen Bakker <jbakker>",
        ),
        "Jesse Yurkovich <jesse.y@gmail.com>": (
            "Jesse Y <deadpin>",
            "Jesse Yurkovich <deadpin>",
        ),
        "Johannes J <johannesj@noreply.localhost>": (
            "Johannes J <johannesj>",
        ),
        "Johnny Matthews <johnny.matthews@gmail.com>": (
            "Johnny Matthews (guitargeek) <johnny.matthews@gmail.com>",
            "Johnny Matthews <guitargeek>",
            "guitargeek <johnny.matthews@gmail.com>",
        ),
        "Jorijn de Graaf <bonj@noreply.localhost>": (
            "Jorijn de Graaf <bonj>",
            "bonj <jorijndegraaf@gmail.com>",
        ),
        "Joseph Eagar <joeedh@gmail.com>": (
            "Joe Eagar <joeedh@gmail.com>",
            "Joseph Eagar <joeedh>",
            "Joseph Eagar <josepheagar@noreply.localhost>",
        ),
        "Josh Maros <joshm-2@noreply.localhost>": (
            "Josh Maros <60271685+joshua-maros@users.noreply.github.com>",
            "joshua-maros <60271685+joshua-maros@users.noreply.github.com>",
        ),
        "Julian Eisel <julian@blender.org>": (
            "Julian Eisel <Severin>",
            "Julian Eisel <eiseljulian@gmail.com>",
            "Julian Eisel <julian@linux-chl2.site>",
            "Julian Eisel <julian_eisel@web.de>",
            "Julian Eisel <julianeisel@Julians-MacBook-Pro.local>",
            "Julian Eisel <julianeisel@noreply.localhost>",
            "Severin <eiseljulian@gmail.com>",
            "Severin <julian_eisel@web.de>",
            "julianeisel <julian_eisel@web.de>",
        ),
        "Julien Kaspar <julien@blender.org>": (
            "Julien Kaspar <JulienKaspar>",
        ),
        "Jun Mizutani <jmztn@noreply.localhost>": (
            "Jun Mizutani <jmztn>",
        ),
        "Jörg Müller <nexyon@gmail.com>": (
            "Joerg Mueller <nexyon@gmail.com>",
        ),
        "Jürgen Herrmann <shadowrom@me.com>": (
            "Juergen Herrmann <shadowrom@me.com>",
        ),
        "Kaspian Jakobsson <kaspian.jakobsson@gmail.com>": (
            "\x96kaspian.jakobssongmail.com <kaspian.jakobsson@gmail.com>",
        ),
        "Kevin C. Burke <kevincburke@noreply.localhost>": (
            "Kevin C. Burke <blastframe>",
        ),
        "Kévin Dietrich <kevin.dietrich@mailoo.org>": (
            "Kevin Dietrich <kevin.dietrich@mailoo.org>",
            "Kévin Dietrich <kevindietrich>",
        ),
        "Leon Schittek <leon.schittek@gmx.net>": (
            "Leon Leno <lone_noel>",
            "Leon Schittek <lone_noel>",
            "Leon Schittek <lone_noel@noreply.localhost>",
        ),
        "Lictex Steaven <lictex_>": (
            "lictex_ <lictex_>",
        ),
        "Luca Rood <dev@lucarood.com>": (
            "Luca Rood <LucaRood>",
        ),
        "Lucas Tadeu Teixeira <lucas@lucastadeu.com>": (
            "Lucas Tadeu <yup_lucas@noreply.localhost>",
        ),
        "Lukas Stockner <lukas.stockner@freenet.de>": (
            "Lukas Stockner <lukasstockner97>",
        ),
        "Lukas Tönne <lukas@blender.org>": (
            "Lukas Toenne <lukas.toenne@googlemail.com>",
            "Lukas Tönne <lukas.toenne@gmail.com>",
            "Lukas Tönne <lukastonne@noreply.localhost>",
        ),
        "Léo Depoix <PiloeGAO>": (
            "PiloeGAO <leonumerique@gmail.com>",
        ),
        "Mai Lavelle <mai.lavelle@gmail.com>": (
            "Mai Lavelle <lavelle@gmail.com>",
        ),
        "Mal Duffin <malachyduffin@gmail.com>": (
            "Mal Duffin <mal_cando>",
        ),
        "Manuel Castilla <manzanillawork@gmail.com>": (
            "Manuel Castilla <manzanilla>",
        ),
        "Marc Chehab <marcchehab@protonmail.ch>": (
            "Marc Chéhab <marcchehab@noreply.localhost>",
            "Marc Chéhab <marcluzmedia>",
        ),
        "Marcos Perez <pistolario>": (
            "Marcos Perez <pistolario@noreply.localhost>",
        ),
        "Martijn Berger <mberger@denc.com>": (
            "Martijn Berger <martijn.berger@gmail.com>",
            "Martijn Berger <mberger@denc.nl>",
            "Martijn Berger <mberger@martijns-mbp.lan>",
        ),
        "Martijn Versteegh <martijn@aaltjegron.nl>": (
            "Martijn Versteegh <Baardaap>",
            "Martijn Versteegh <baardaap@noreply.localhost>",
            "Martijn Versteegh <blender@aaltjegron.nl>",
        ),
        "Matias Mendiola <matias.mendiola@gmail.com>": (
            "Matias Mendiola <mendio>",
        ),
        "Matt Heimlich <matt.heimlich@gmail.com>": (
            "Matt Heimlich <m9105826>",
        ),
        "Matteo F. Vescovi <mfvescovi@gmail.com>": (
            "Matteo F. Vescovi <mfv>",
        ),
        "Max Schlecht <bobbe@noreply.localhost>": (
            "Max Schlecht <Bobbe>",
        ),
        "Maxime Casas <maxime_casas@orange.fr>": (
            "Maxime Casas <troopy28>",
        ),
        "Michael Jones <michael_p_jones@apple.com>": (
            "Michael Jones (Apple) <michael-jones@noreply.localhost>",
            "Michael Jones <michael_jones>",
        ),
        "Michael Kowalski <makowalski@nvidia.com>": (
            "Michael Kowalski <makowalski>",
            "Michael Kowalski <makowalski@noreply.localhost>",
        ),
        "Miguel Pozo <pragma37@gmail.com>": (
            "Miguel Pozo <pragma37>",
            "Miguel Pozo <pragma37@noreply.localhost>",
        ),
        "Mikhail Matrosov <ktdfly>": (
            "Mikhail <ktdfly>",
            "Mikhail Matrosov <kdtfly>",
        ),
        "Monique Dewanchand <m.dewanchand@atmind.nl>": (
            "Monique Dewanchand <mdewanchand>",
        ),
        "Nate Rupsis <nrupsis@gmail.com>": (
            "Nate Rupsis <C-Nathaniel.Rupsis@charter.com>",
            "Nate Rupsis <C-nathaniel.rupsis@charter.com>",
            "Nate Rupsis <nrupsis>",
            "Nate Rupsis <nrupsis@noreply.localhost>",
        ),
        "Nathan Craddock <nzcraddock@gmail.com>": (
            "Nathan Craddock <Zachman>",
        ),
        "Nathan Letwory <nathan@blender.org>": (
            "Nathan Letwory <jesterking>",
            "Nathan Letwory <nathan@letworyinteractive.com>",
            "Nathan Letwory <nathan@mcneel.com>",
        ),
        "Nathan Vegdahl <cessen@cessen.com>": (
            "Nathan Vegdahl <cessen>",
        ),
        "Nicholas Bishop <nicholasbishop@gmail.com>": (
            "Nicholas Bishop <nicholas.bishop@floored.com>",
        ),
        "Nicholas Rishel <rishel.nick@gmail.com>": (
            "Nicholas Rishel <nicholas_rishel>",
        ),
        "Nick Milios <semaphore>": (
            "milios <n_mhlios@hotmail.com>",
        ),
        "Nikita Sirgienko <nikita.sirgienko@intel.com>": (
            "Nikita Sirgienko <sirgienko>",
        ),
        "Omar Emara <mail@OmarEmara.dev>": (
            "Omar Emara <OmarSquircleArt>",
            "OmarSquircleArt <mail@OmarEmara.dev>",
            "OmarSquircleArt <omar.squircleart@gmail.com>",
        ),
        "Pablo Dobarro <pablodp606@gmail.com>": (
            "Pablo Dobarro <pablodp606>",
        ),
        "Pablo Vazquez <pablo@blender.org>": (
            "Pablo Vazquez <contact@pablovazquez.art>",
            "Pablo Vazquez <pablovazquez>",
            "Pablo Vazquez <venomgfx@gmail.com>",
        ),
        "Pascal Schoen <pascal.schoen@adidas-group.com>": (
            "Pascal Schön <VanCantus>",
        ),
        "Patrick Busch <xylvier@noreply.localhost>": (
            "Patrick Busch <Xylvier>",
        ),
        "Patrick Mours <pmours@nvidia.com>": (
            "Patrick Mours <pmoursnv@noreply.localhost>",
        ),
        "Paul Golter <paulgolter>": (
            "Paul Golter <pullpullson>",
        ),
        "Philipp Oeser <philipp@blender.org>": (
            "Philipp Oeser <info@graphics-engineer.com>",
            "Philipp Oeser <lichtwerk>",
            "Philipp Oeser <lichtwerk@noreply.localhost>",
            "Philipp Oeser <noreply@developer.blender.org>",
            "Philipp Oeser <poeser@posteo.de>",
        ),
        "Pratik Borhade <pratikborhade302@gmail.com>": (
            "Pratik Borhade <PratikPB2123>",
        ),
        "Ray Molenkamp <github@lazydodo.com>": (
            "Lazydodo <github@lazydodo.com>",
            "Ray Molenkamp <LazyDodo>",
            "Ray molenkamp <LazyDodo>",
            "Ray molenkamp <lazydodo@noreply.localhost>",
            "lazydodo <github@lazydodo.com>",
        ),
        "Red Mser <RedMser>": (
            "RedMser <RedMser>",
            "RedMser <redmser.jj2@gmail.com>",
        ),
        "Richard Antalik <richardantalik@gmail.com>": (
            "Richard Antalik <ISS>",
            "Richard Antalik <iss@noreply.localhost>",
        ),
        "Robert Guetzkow <gitcommit@outlook.de>": (
            "Robert Guetzkow <rjg>",
        ),
        "Robin Hohnsbeen <robin@hohnsbeen.de>": (
            "Robin Hohnsbeen <robin-4@noreply.localhost>",
        ),
        "Sahar A. Kashi <sahar.alipourkashi@amd.com>": (
            "Sahar A. Kashi <salipour@noreply.localhost>",
            "salipourto <sahar.alipourkashi@amd.com>",
        ),
        "Sebastian Herholz <sebastian.herholz@intel.com>": (
            "Sebastian Herholz <Sebastian.Herholz@gmail.com>",
            "Sebastian Herholz <sherholz>",
            "Sebastian Herholz <sherholz@noreply.localhost>",
            "Sebastian Herhoz <sebastian.herholz@intel.com>",
        ),
        "Sebastian Koenig <sebastiankoenig@posteo.de>": (
            "Sebastian Koenig <sebastian_k>",
            "Sebastian Koenig <sebastian_k@gmail.com>",
        ),
        "Sebastian Parborg <darkdefende@gmail.com>": (
            "Sebastian Parborg <zeddb>",
            "Sebastian Parborg <zeddb@noreply.localhost>",
            "Sebastian Ramacher <sramacher@debian.org>",
        ),
        "Sergey Sharybin <sergey@blender.org>": (
            "Sergey Sharybin <sergey.vfx@gmail.com>",
            "Sergey Sharybin <sergey>",
            "Sergey Sharybin <sergey@noreply.localhost>",
            "blender <sergey.vfx@gmail.com>",
        ),
        "Shane Ambler <Shane@ShaneWare.Biz>": (
            "Shane Ambler <shaneambler@noreply.localhost>",
        ),
        "Shashank Shekhar <secondary.cmdr2@gmail.com>": (
            "Shashank Shekhar <cmdr2>",
        ),
        "Siddhartha Jejurkar <f20180617@goa.bits-pilani.ac.in>": (
            "Siddhartha Jejurkar <sidd017>",
        ),
        "Sietse Brouwer <sietse@hetvrijeoog.nl>": (
            "Sietse Brouwer <SietseB>",
        ),
        "Simon G <intrigus>": (
            "Simon <intrigus>",
        ),
        "Sonny Campbell <sonny.campbell@unity3d.com>": (
            "DESKTOP-ON14TH5\\Sonny Campbell <sonny.campbell@unity3d.com>",
            "Sonny Campbell (@SonnyCampbell_Unity) <>",
            "Sonny Campbell <SonnyCampbell_Unity>",
            "Sonny Campbell <sonnycampbell_unity@noreply.localhost>",
        ),
        "Stefan Werner <stefan.werner@intel.com>": (
            "Stefan Werner <stefan.werner@tangent-animation.com>",
            "Stefan Werner <stefan@keindesign.de>",
            "Stefan Werner <stefan_werner@noreply.localhost>",
            "Stefan Werner <stewreo@gmail.com>",
            "Stefan Werner <swerner@smithmicro.com>",
            "Werner, Stefan <stefan.werner@intel.com>",
        ),
        "Stephan Seitz <theHamsta>": (
            "Stephan <theHamsta>",
        ),
        "Sybren A. Stüvel <sybren@blender.org>": (
            "Sybren A. StÃ\x83Â¼vel <sybren@stuvel.eu>",
            "Sybren A. Stüvel <sybren>",
            "Sybren A. Stüvel <sybren@stuvel.eu>",
        ),
        "Thomas Dinges <thomas@blender.org>": (
            "Thomas Dinges <blender@dingto.org>",
            "Thomas Dinges <dingto>",
        ),
        "Thomas Szepe <HG1_public@gmx.net>": (
            "HG1 <HG1_public@gmx.net>",
        ),
        "Tom Edwards <contact@steamreview.org>": (
            "Tom Edwards <artfunkel>",
        ),
        "Tristan Porteries <republicthunderbolt9@gmail.com>": (
            "Porteries Tristan <republicthunderbolt9@gmail.com>",
        ),
        "Troy Sobotka <troy.sobotka@gmail.com>": (
            "Troy Sobotka <sobotka>",
        ),
        "Tuomo Keskitalo <tuomo.keskitalo@iki.fi>": (
            "Tuomo Keskitalo <tkeskita>",
        ),
        "Ulysse Martin <you.le@live.fr>": (
            "Ulysse Martin <youle>",
        ),
        "Vasyl Pidhirskyi <vpidhirskyi@gmail.com>": (
            "Vasyl-Pidhirskyi <vpidhirskyi@gmail.com>",
        ),
        "Vitor Boschi <vitorboschi@gmail.com>": (
            "Vitor Boschi <vitorboschi>",
            "Vitor Boschi da Silva <vitorboschi>"
        ),
        "Vuk Gardašević <lijenstina>": (
            "Vuk GardaÅ¡eviÄ\x87 <lijenstina>",
        ),
        "Wayde Moss <wbmoss_dev@yahoo.com>": (
            "Wayde Moss <GuiltyGhost>",
        ),
        "Weizhen Huang <weizhen@blender.org>": (
            "RiverIntheSky <itsnotrj@hotmail.com>",
            "Weizhen Huang <itsnotrj@gmail.com>",
            "Weizhen Huang <weizhen@noreply.localhost>",
        ),
        "Welp <jtf515@gmail.com>": (
            "Jake <Welp>",
        ),
        "William Leeson <william@blender.org>": (
            "William Leeson <leesonw>",
            "William Leeson <william.leeson@gmail.com>",
        ),
        "William Reynish <william@reynish.com>": (
            "William Reynish <billrey>",
            "William Reynish <billrey@me.com>",
            "William Reynish <billreynish>",
        ),
        "Willian Padovani Germano <wpgermano@gmail.com>": (
            "ianwill <wpgermano@gmail.com>",
        ),
        "Xavier Hallade <xavier.hallade@intel.com>": (
            "Xavier Hallade <xavierh@noreply.localhost>",
        ),
        "Yann Lanthony <yann-lty>": (
            "@yann-lty <>",
        ),
        "Yiming Wu <xp8110@outlook.com>": (
            "ChengduLittleA <xp8110@outlook.com>",
            "YimingWu <NicksBest>",
            "YimingWu <chengdulittlea@noreply.localhost>",
            "YimingWu <xp8110@outlook.com>",
            "YimingWu <xp8110t@outlook.com>",
        ),
        "jon denning <gfxcoder@gmail.com>": (
            "Jon Denning <gfxcoder>",
        ),
        "nBurn <nbwashburn@gmail.com>": (
            "nBurn <nBurn>",
        ),
        "nutti <nutti.metro@gmail.com>": (
            "nutti <Nutti>",
        ),
        "ok_what <ip1149a@gmail.com>": (
            "ok what <ok_what>",
        ),
    }

    # Some validation, ensure ordered, consistent to help with maintenance.
    keys = list(author_map_valid_to_invalid.keys())
    for i, (key, key_ordered) in enumerate(zip(keys, sorted(keys))):
        if key != key_ordered:
            raise RuntimeError((
                "Names unordered: {:d}\n"
                "  {:s} ~ (found)\n"
                "  {:s} ~ (expected)\n"
                ""
            ).format(i, key, key_ordered))

    for i, (key, value) in enumerate(author_map_valid_to_invalid.items()):
        if value != tuple(sorted(value)):
            raise RuntimeError("Name values: {:s} at index {:d} is not ordered".format(key, i))
        if len(set(value)) != len(value):
            raise RuntimeError("Name values: {:s} at index {:d} contains duplicate values".format(key, i))
        if key in value:
            raise RuntimeError("Name values: {:s} at index {:d} contains the key in the values body".format(key, i))

    table = {}
    for key, values in author_map_valid_to_invalid.items():
        for value_old in values:
            table[value_old] = key
    return table
