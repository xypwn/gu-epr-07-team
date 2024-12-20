__author__ = "8030456, Schuppan, 8404886, Kraus"

class Util:
    """This has no reason to be a class."""
    def column_align(rows: list[list[str]], sep: str = " ", pad: str = " ") -> str:
        """Column-aligns all cells in the given list.

        >>> print(column_align([["a", "abc"], ["abc", "a"]]))
        a   abc
        abc a
        >>> print(column_align([["a", "abc"], ["abc", "a"], ["abcd"]]))
        a    abc
        abc  a
        abcd
        >>> print(column_align([["a", "ab", "a"], ["a", "a"], ["a"] * 4]))
        a ab a
        a a
        a a  a a
        >>> print(column_align([["a", "abc"], ["abc", "a"]], sep="_", pad="."))
        a.._abc
        abc_a
        """
        # Number of cells of the row with the most cells.
        max_cols = max(len(row) for row in rows)
        # Length of the largest cell in each column.
        max_col_widths = [
            # For each set of cells in a column, get the length of the largest
            # cell.
            max(
                len(rows[row_idx][col_idx]) if col_idx < len(rows[row_idx]) else 0
                for row_idx in range(len(rows))
            )
            for col_idx in range(max_cols)
        ]
        return "\n".join(
            sep.join(
                # Pad each cell so it aligns with all other
                # cells in that column.
                cell
                + (
                    pad
                    * (
                        max_col_widths[col_idx] - len(cell)
                        if col_idx < len(row) - 1
                        else 0
                    )
                )
                for col_idx, cell in enumerate(row)
            )
            for row in rows
        )
