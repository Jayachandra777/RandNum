from pyteal import *

is_creator = Txn.sender() == Global.creator_address()

def initialize_game_params(ticketing_start, ticketing_duration, ticket_fee, withdrawal_start, win_multiplier, max_guess_number, max_players_allowed, lottery_account, create_txn):
    return Seq(
        Assert(
            And(
                # Make sure lottery contract has been reset
                App.localGetEx(Int(0), Bytes("Ticketing_Start")) == Int(0),
                App.localGetEx(Int(0), Bytes("Ticketing_Duration")) == Int(0),
                App.localGetEx(Int(0), Bytes("Withdrawal_Start")) == Int(0),
                App.localGetEx(Int(0), Bytes("Lucky_Number")) == Int(0),
                App.localGetEx(Int(0), Bytes("Ticket_Fee")) == Int(0),
                App.localGetEx(Int(0), Bytes("Win_Multiplier")) == Int(0),
                App.localGetEx(Int(0), Bytes("Max_Players_Allowed")) == Int(0),
                App.localGetEx(Int(0), Bytes("Max_Guess_Number")) == Int(0),
                App.localGetEx(Int(0), Bytes("Players_Ticket_Bought")) == Int(0),
                App.localGetEx(Int(0), Bytes("Players_Ticket_Checked")) == Int(0),
                App.localGetEx(Int(0), Bytes("Players_Won")) == Int(0),
                App.localGetEx(Int(0), Bytes("Game_Master")) == Global.zero_address(),
                App.localGetEx(Int(0), Bytes("Game_Master_Deposit")) == Int(0),
                create_txn.receiver() == Global.current_application_address(),
                create_txn.sender() == Txn.sender(),
                create_txn.type_enum() == TxnType.Payment,
                create_txn.amount() >= Int(1000000),
                create_txn.amount() + Balance(lottery_account) - MinBalance(lottery_account) > max_players_allowed * (win_multiplier - Int(1)) * ticket_fee,
                create_txn.note() == Bytes("init_game"),
                ticketing_start > Global.latest_timestamp() + Int(180),
                ticketing_duration > Int(900),
                ticket_fee >= Int(1000000),
                max_guess_number > Int(99),
                max_players_allowed > Int(0),
                win_multiplier > Int(1),
                withdrawal_start > ticketing_start + ticketing_duration + Int(900)
            )
        ),
        App.localPut(Int(0), Bytes("Ticketing_Start"), ticketing_start),
        App.localPut(Int(0), Bytes("Ticketing_Duration"), ticketing_duration),
        App.localPut(Int(0), Bytes("Withdrawal_Start"), withdrawal_start),
        App.localPut(Int(0), Bytes("Ticket_Fee"), ticket_fee),
        App.localPut(Int(0), Bytes("Win_Multiplier"), win_multiplier),
        App.localPut(Int(0), Bytes("Max_Players_Allowed"), max_players_allowed),
        App.localPut(Int(0), Bytes("Max_Guess_Number"), max_guess_number),
        App.localPut(Int(0), Bytes("Game_Master"), Txn.sender()),
        App.localPut(Int(0), Bytes("Game_Master_Deposit"), create_txn.amount())
    )

def enter_game(guess_number, ticket_txn):
    return Seq(
        Assert(
            And(
                App.localGetEx(Int(0), Bytes("Players_Ticket_Bought")) < App.localGetEx(Int(0), Bytes("Max_Players_Allowed")),
                guess_number > Int(0),
                guess_number <= App.localGetEx(Int(0), Bytes("Max_Guess_Number")),
                ticket_txn.receiver() == Global.current_application_address(),
                ticket_txn.sender() == Txn.sender(),
                ticket_txn.amount() == App.localGetEx(Int(0), Bytes("Ticket_Fee")),
                ticket_txn.type_enum() == TxnType.Payment,
                ticket_txn.note() == Bytes("buy_ticket")
            )
        ),
        App.localPut(Int(0), Bytes("Players_Ticket_Bought"), App.localGetEx(Int(0), Bytes("Players_Ticket_Bought")) + Int(1)),
        App.localPut(Int(1), Txn.sender(), guess_number)
    )

def check_tickets():
    guessed_numbers = App.localGetKeys(Int(1))
    total_players = App.localGetEx(Int(0), Bytes("Players_Ticket_Bought"))
    lucky_number = App.localGetEx(Int(0), Bytes("Lucky_Number"))

    return Seq(
        Assert(
            And(
                App.localGetEx(Int(0), Bytes("Ticketing_Start")) > Int(0),
                App.localGetEx(Int(0), Bytes("Ticketing_Start")) + App.localGetEx(Int(0), Bytes("Ticketing_Duration")) < Global.latest_timestamp(),
                lucky_number == Int(0)
            )
        ),
        App.localPut(Int(0), Bytes("Lucky_Number"), Sha256(Arg(0))),
        If(len(guessed_numbers) > Int(0),
            Seq([
                App.localPut(Int(0), Bytes("Players_Ticket_Checked"), total_players),
                ForEach(guessed_numbers, lambda index: Seq(
                    If(App.localGetEx(Int(1), index) == lucky_number,
                        Seq(
                            App.localPut(Int(2), index, Int(1)),
                            App.localPut(Int(0), Bytes("Players_Won"), App.localGetEx(Int(0), Bytes("Players_Won")) + Int(1))
                        ),
                        App.localPut(Int(2), index, Int(0))
                    ),
                )),
            ])
        )
    )

def reset_game(reset_txn):
    return Seq(
        Assert(
            And(
                is_creator,
                App.localGetEx(Int(0), Bytes("Withdrawal_Start")) > Int(0),
                Global.latest_timestamp() >= App.localGetEx(Int(0), Bytes("Withdrawal_Start")),
                reset_txn.receiver() == Global.current_application_address(),
                reset_txn.sender() == Global.creator_address(),
                reset_txn.type_enum() == TxnType.Payment,
                reset_txn.amount() == Int(0),
                reset_txn.note() == Bytes("reset_game")
            )
        ),
        App.localPut(Int(0), Bytes("Ticketing_Start"), Int(0)),
        App.localPut(Int(0), Bytes("Ticketing_Duration"), Int(0)),
        App.localPut(Int(0), Bytes("Withdrawal_Start"), Int(0)),
        App.localPut(Int(0), Bytes("Lucky_Number"), Int(0)),
        App.localPut(Int(0), Bytes("Ticket_Fee"), Int(0)),
        App.localPut(Int(0), Bytes("Win_Multiplier"), Int(0)),
        App.localPut(Int(0), Bytes("Max_Players_Allowed"), Int(0)),
        App.localPut(Int(0), Bytes("Max_Guess_Number"), Int(0)),
        App.localPut(Int(0), Bytes("Players_Ticket_Bought"), Int(0)),
        App.localPut(Int(0), Bytes("Players_Ticket_Checked"), Int(0)),
        App.localPut(Int(0), Bytes("Players_Won"), Int(0)),
        App.localPut(Int(0), Bytes("Game_Master"), Global.zero_address()),
        App.localPut(Int(0), Bytes("Game_Master_Deposit"), Int(0))
    )

def withdrawal():
    return Seq(
        Assert(
            And(
                App.localGetEx(Int(0), Bytes("Withdrawal_Start")) > Int(0),
                Global.latest_timestamp() >= App.localGetEx(Int(0), Bytes("Withdrawal_Start"))
            )
        ),
        App.localPut(Int(0), Bytes("Withdrawal_Start"), Int(0)),
        App.localPut(Int(0), Bytes("Game_Master_Deposit"), Int(0))
    )

def contract():
    on_initialize = initialize_game_params(Int(0), Int(0), Int(0), Int(0), Int(0), Int(0), Int(0), Global.zero_address(), Txn)
    on_enter = enter_game(Int(0), Txn)
    on_check_tickets = check_tickets()
    on_reset = reset_game(Txn)
    on_withdrawal = withdrawal()

    return Cond(
        [Txn.application_id() == Int(0), on_initialize],
        [Txn.application_id() != Int(0), Cond(
            [Txn.application_id() == Int(0), on_initialize],
            [Txn.application_id() != Int(0), Cond(
                [Txn.application_id() == App.id(), Cond(
                    [Txn.application_id() == App.id() and Txn.application_id() == Int(0), on_initialize],
                    [Txn.application_id() == App.id() and Txn.application_id() != Int(0), Cond(
                        [Txn.application_id() == App.id() and Txn.application_id() == App.id(), Cond(
                            [Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() == Int(0), on_initialize],
                            [Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() != Int(0), Cond(
                                [Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() == App.id(), Cond(
                                    [Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() == Int(0), on_initialize],
                                    [Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() == App.id() and Txn.application_id() != Int(0), Seq(on_enter, on_check_tickets, on_reset, on_withdrawal)]
                                )]
                            )]
                        )]
                    )]
                )]
            )]
        )]
    )

if __name__ == "__main__":
    print(compileTeal(contract(), mode=Mode.Application))
