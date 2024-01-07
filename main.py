import coc
import asyncio

import asyncio
import coc


async def main():
    async with coc.Client() as coc_client:
        try:
            await coc_client.login("fejlur2137@gmail.com", "password")
        except coc.invalidcredentials as error:
            exit(error)

        player = await coc_client.get_player("tag")
        print(f"{player.name} has {player.trophies} trophies!")

        clans = await coc_client.search_clans(name="best clan ever", limit=5)
        for clan in clans:
            print(f"{clan.name} ({clan.tag}) has {clan.member_count} members")

        try:
            war = await coc_client.get_current_war("#clantag")
            print(f"{war.clan_tag} is currently in {war.state} state.")
        except coc.privatewarlog:
            print("uh oh, they have a private war log!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass